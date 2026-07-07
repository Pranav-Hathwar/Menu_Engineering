"""File ingestion pipeline for messy restaurant sales exports."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import logging
import re
import uuid
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.sales import SalesData
from app.models.upload_batch import UploadBatch

logger = logging.getLogger(__name__)

HEADER_KEYWORDS = {
    "item_name": ["item", "name", "product", "menu", "desc", "description", "dish", "sku"],
    "quantity": ["qty", "quantity", "count", "sold", "volume", "units", "orders"],
    "revenue": ["revenue", "sales", "amount", "total", "gross", "net", "turnover", "value", "price"],
    "unit_cost": ["unitcost", "cost", "cogs", "expense", "purchase", "ingredient"],
    "date": ["date", "time", "day", "businessdate", "orderdate"],
}

JUNK_ITEM_NAMES = {"", "nan", "none", "null", "total", "subtotal", "grandtotal", "summary"}


def process_upload(
    file_bytes: bytes,
    filename: str,
    db: Session,
    restaurant_name: str,
    owner_id: int | None = None,
    allow_duplicate: bool = False,
    report_date: dt.date | None = None,
    date_hint: dt.date | None = None,
):
    restaurant_name = restaurant_name.strip()
    content_hash = hashlib.sha256(file_bytes).hexdigest()

    # Duplicate guard: an identical file re-uploaded to the same restaurant
    # would silently double-count revenue. Reject unless explicitly overridden.
    if not allow_duplicate:
        existing = (
            db.query(UploadBatch)
            .filter(
                UploadBatch.owner_id == owner_id,
                UploadBatch.restaurant_name == restaurant_name,
                UploadBatch.content_hash == content_hash,
            )
            .order_by(UploadBatch.created_at.desc())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"This exact file was already uploaded to '{restaurant_name}' "
                    f"(batch {existing.batch_id[:8]}, {existing.row_count} rows). "
                    "Re-uploading would double-count revenue. "
                    "Use 'Upload anyway' to override."
                ),
            )

    dataframe = _read_dataframe(file_bytes, filename)

    # Daily POS exports often carry the report date OUTSIDE the table — in the
    # filename ("Sales_30-07-2025.xlsx") or in title rows above the header.
    # Resolve a fallback date before those rows are discarded. Precedence:
    # a human-entered report_date, then a date detected in filename/title
    # text, then a soft hint (e.g. the sent date of the email that carried
    # the file), then the upload day.
    detected_date = _extract_context_date(filename, dataframe)
    if report_date is not None:
        fallback_date, fallback_source = report_date, "provided"
    elif detected_date is not None:
        fallback_date, fallback_source = detected_date, "detected"
    elif date_hint is not None:
        fallback_date, fallback_source = date_hint, "email-date"
    else:
        fallback_date, fallback_source = dt.date.today(), "upload-day"

    dataframe = _discover_headers(dataframe)
    dataframe = _normalize_columns(dataframe)
    records, metadata = _normalize_sales_records(dataframe, fallback_date=fallback_date, fallback_source=fallback_source)

    if not records:
        raise HTTPException(
            status_code=400,
            detail="The file was readable, but no valid sales rows with item and revenue could be extracted.",
        )

    batch_id = str(uuid.uuid4())
    sales_objects = [
        SalesData(
            **record,
            restaurant_name=restaurant_name,
            owner_id=owner_id,
            upload_batch_id=batch_id,
        )
        for record in records
    ]

    total_revenue = sum(record["revenue"] for record in records)
    total_units = sum(record["quantity"] for record in records)

    db.add_all(sales_objects)
    db.add(
        UploadBatch(
            batch_id=batch_id,
            owner_id=owner_id,
            restaurant_name=restaurant_name,
            filename=filename,
            content_hash=content_hash,
            row_count=len(sales_objects),
            total_revenue=round(total_revenue, 2),
        )
    )
    db.commit()

    logger.info(
        "Ingested %s rows for restaurant=%s owner_id=%s batch=%s",
        len(sales_objects),
        restaurant_name,
        owner_id,
        batch_id,
    )

    return {
        "message": f"Successfully ingested {len(sales_objects)} rows.",
        "rows_ingested": len(sales_objects),
        "rows_rejected": metadata["rows_rejected"],
        "total_revenue": round(total_revenue, 2),
        "total_units": int(total_units),
        "upload_batch_id": batch_id,
        "detected_columns": metadata["detected_columns"],
        "dates_defaulted": metadata.get("dates_defaulted", 0),
        # "column" when dates came from the file's own date column; otherwise
        # "provided" / "detected" / "upload-day" with the date that was applied.
        "date_mode": metadata.get("date_mode", "column"),
        "applied_date": metadata.get("applied_date"),
    }


def list_upload_batches(
    db: Session,
    owner_id: int | None,
    restaurant_name: str | None = None,
):
    query = db.query(UploadBatch).filter(UploadBatch.owner_id == owner_id)
    if restaurant_name:
        query = query.filter(UploadBatch.restaurant_name == restaurant_name)
    batches = query.order_by(UploadBatch.created_at.desc(), UploadBatch.id.desc()).all()
    return [
        {
            "batch_id": b.batch_id,
            "restaurant_name": b.restaurant_name,
            "filename": b.filename,
            "row_count": b.row_count,
            "total_revenue": b.total_revenue,
            "created_at": b.created_at,
        }
        for b in batches
    ]


def delete_upload_batch(db: Session, owner_id: int | None, batch_id: str) -> int:
    """Delete a batch and its sales rows (owner-scoped). Returns rows removed."""
    batch = (
        db.query(UploadBatch)
        .filter(UploadBatch.owner_id == owner_id, UploadBatch.batch_id == batch_id)
        .first()
    )
    if batch is None:
        raise HTTPException(status_code=404, detail="Upload batch not found.")

    deleted = (
        db.query(SalesData)
        .filter(SalesData.owner_id == owner_id, SalesData.upload_batch_id == batch_id)
        .delete(synchronize_session=False)
    )
    db.delete(batch)
    db.commit()
    logger.info("Deleted batch %s (%s sales rows) for owner_id=%s", batch_id, deleted, owner_id)
    return deleted


def _read_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    suffix = (filename or "").lower().rsplit(".", 1)[-1]
    buffer = io.BytesIO(file_bytes)

    try:
        if suffix in {"xlsx", "xls"}:
            sheets = pd.read_excel(buffer, sheet_name=None)
            frames = [frame.assign(source_sheet=sheet) for sheet, frame in sheets.items() if not frame.empty]
            return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        if suffix == "json":
            return _read_json_dataframe(file_bytes)

        return _read_csv_dataframe(file_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("File parsing failed for %s", filename)
        raise HTTPException(status_code=400, detail=f"Could not parse the uploaded file: {exc}") from exc


def _read_csv_dataframe(file_bytes: bytes) -> pd.DataFrame:
    """Parse delimited text robustly, tolerating messy real-world exports.

    Uses the stdlib csv module rather than pandas' CSV reader because POS
    exports frequently have *ragged* rows (metadata/title rows with fewer
    columns than the data rows). pandas raises "Expected N fields, saw M" on
    those; csv.reader simply yields rows of varying length, which we pad to a
    uniform width. Quoted fields containing the delimiter (e.g. "Rs 4,000")
    are handled correctly.
    """
    text = _decode_bytes(file_bytes)
    if not text.strip():
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    delimiter = _sniff_delimiter(text)

    try:
        rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CSV parsing failed: {exc}") from exc

    # Drop fully blank rows and pad ragged rows to the widest row.
    rows = [row for row in rows if any(str(cell).strip() for cell in row)]
    if not rows:
        raise HTTPException(status_code=400, detail="The uploaded file has no data rows.")

    width = max(len(row) for row in rows)
    padded = [row + [None] * (width - len(row)) for row in rows]

    # header=None: every row is data. _discover_headers promotes the real
    # header row, so clean and messy files take the same path.
    return pd.DataFrame(padded)


def _decode_bytes(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return file_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_bytes.decode("latin1", errors="replace")


def _sniff_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except Exception:
        # Fall back to the most common delimiter present, defaulting to comma.
        counts = {d: sample.count(d) for d in (",", ";", "\t", "|")}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","


def _read_json_dataframe(file_bytes: bytes) -> pd.DataFrame:
    try:
        payload = json.loads(file_bytes.decode("utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"JSON parsing failed: {exc}") from exc

    records = _extract_json_records(payload)
    if not records:
        raise HTTPException(status_code=400, detail="JSON file did not contain a usable record list.")
    return pd.json_normalize(records)


def _extract_json_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if all(not isinstance(value, (dict, list)) for value in payload.values()):
            return [payload]
        for key in ("sales", "items", "orders", "data", "records", "rows", "transactions"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for value in payload.values():
            records = _extract_json_records(value)
            if records:
                return records
    return []


def _discover_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all", axis=1).dropna(how="all", axis=0).reset_index(drop=True)
    if df.empty or len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    header_score = _keyword_score(" ".join(str(col) for col in df.columns))
    if header_score >= 2:
        return df

    for idx, row in df.head(30).iterrows():
        score = _keyword_score(" ".join(str(value) for value in row.tolist()))
        if score >= 2:
            df = df.iloc[idx + 1 :].reset_index(drop=True)
            df.columns = row.astype(str).tolist()
            return df
    return df


def _keyword_score(text: str) -> int:
    normalized = _normalize_token(text)
    return sum(1 for aliases in HEADER_KEYWORDS.values() for alias in aliases if alias in normalized)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_normalize_token(col) or f"column{idx}" for idx, col in enumerate(df.columns)]
    return df.loc[:, ~pd.Index(df.columns).duplicated()]


def _normalize_sales_records(
    df: pd.DataFrame,
    fallback_date: dt.date | None = None,
    fallback_source: str = "upload-day",
):
    fallback_date = fallback_date or dt.date.today()
    mapped = _map_columns(df)
    working = pd.DataFrame()
    working["item_name"] = df[mapped["item_name"]].astype(str).str.strip()

    quantity_source = mapped.get("quantity")
    working["quantity"] = _to_number(df[quantity_source]) if quantity_source else 1

    unit_cost_source = mapped.get("unit_cost")
    working["unit_cost"] = _to_number(df[unit_cost_source]) if unit_cost_source else 0.0

    revenue_source = mapped.get("revenue")
    if revenue_source:
        working["revenue"] = _to_number(df[revenue_source])
    else:
        working["revenue"] = 0.0

    unit_price_source = mapped.get("unit_price")
    if unit_price_source and (working["revenue"].fillna(0) <= 0).all():
        working["revenue"] = _to_number(df[unit_price_source]) * working["quantity"].fillna(1)

    date_source = mapped.get("date")
    if date_source:
        working["date"] = _parse_dates(df[date_source])
    else:
        working["date"] = None

    working["item_name"] = working["item_name"].str.replace(r"\s+", " ", regex=True).str.title()
    working["quantity"] = working["quantity"].fillna(1).clip(lower=0).round().astype(int)
    working["revenue"] = working["revenue"].fillna(0.0).clip(lower=0).astype(float)
    working["unit_cost"] = working["unit_cost"].fillna(0.0).clip(lower=0).astype(float)

    # Rows whose date could not be parsed fall back to the file's most common
    # parsed date (the batch almost certainly covers the same period). When the
    # file has no usable date at all, the resolved fallback applies: a date the
    # uploader provided, one detected in the filename/title rows, or upload day.
    parsed_dates = working["date"].dropna()
    if not parsed_dates.empty:
        row_fallback = parsed_dates.mode().iloc[0]
        date_mode = "column"
    else:
        row_fallback = fallback_date
        date_mode = fallback_source
    date_was_defaulted = working["date"].isna()
    working["date"] = working["date"].apply(lambda value: value if pd.notna(value) else row_fallback)

    initial_rows = len(working)
    valid = working[
        working["item_name"].map(lambda value: _normalize_token(value) not in JUNK_ITEM_NAMES)
        & (working["revenue"] > 0)
        & (working["quantity"] > 0)
    ]

    records = valid[["item_name", "quantity", "revenue", "unit_cost", "date"]].to_dict(orient="records")
    return records, {
        "rows_rejected": initial_rows - len(records),
        "detected_columns": mapped,
        # Only count defaults on rows that were actually ingested — a junk
        # summary row with no date is rejected anyway and shouldn't alarm the user.
        "dates_defaulted": int(date_was_defaulted[valid.index].sum()),
        "date_mode": date_mode,
        "applied_date": str(row_fallback) if date_mode != "column" else None,
    }


_MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _extract_context_date(filename: str, df: pd.DataFrame) -> dt.date | None:
    """Find the report date OUTSIDE the data table: filename first (most
    reliable, e.g. "Sales_30-07-2025.xlsx"), then the first rows of the raw
    frame, which still include any title/metadata lines at this stage."""
    candidates = [filename or ""]
    candidates.append(" ".join(str(col) for col in df.columns))
    for _, row in df.head(10).iterrows():
        candidates.append(" ".join(str(value) for value in row.tolist() if pd.notna(value)))

    for text in candidates:
        found = _find_date_in_text(text)
        if found:
            return found
    return None


def _find_date_in_text(text: str) -> dt.date | None:
    text = str(text).lower()
    # "\b" can't see a boundary in "sales_30-07-2025" or "sales30072025":
    # underscores are word characters and letters touch digits. Normalize
    # both so the date patterns can anchor.
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", text)

    # ISO: 2025-07-30 (also 2025/07/30, 2025.07.30)
    match = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if match:
        return _safe_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    # Numeric with 4-digit year: 30-07-2025, 30/7/2025, 30 7 2025, 30.07.2025.
    match = re.search(r"\b(\d{1,2})[-/. ](\d{1,2})[-/. ](20\d{2})\b", text)
    if match:
        first, second, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        # Disambiguate D/M vs M/D: a value over 12 must be the day; ties are
        # read day-first, consistent with the column parser.
        if first > 12 >= second:
            return _safe_date(year, second, first)
        if second > 12 >= first:
            return _safe_date(year, first, second)
        return _safe_date(year, second, first)

    # Month name: "30 July 2025", "July 30, 2025", "30-Jul-25".
    match = re.search(r"\b(\d{1,2})[-/. ]*([a-z]{3,9})[-,/. ]*(20\d{2}|\d{2})\b", text)
    if not match:
        match = re.search(r"\b([a-z]{3,9})[-/. ]*(\d{1,2})[-,/. ]*(20\d{2})\b", text)
        if match:
            month = _MONTH_NAMES.get(match.group(1)[:3])
            if month:
                return _safe_date(int(match.group(3)), month, int(match.group(2)))
        return None
    month = _MONTH_NAMES.get(match.group(2)[:3])
    if month:
        year = int(match.group(3))
        if year < 100:
            year += 2000
        return _safe_date(year, month, int(match.group(1)))
    return None


def _safe_date(year: int, month: int, day: int) -> dt.date | None:
    try:
        candidate = dt.date(year, month, day)
    except ValueError:
        return None
    # Sanity window: a "report date" decades away is a false positive.
    if dt.date(2000, 1, 1) <= candidate <= dt.date.today() + dt.timedelta(days=366):
        return candidate
    return None


def _parse_dates(series) -> pd.Series:
    """Parse a date column accurately across common POS export formats.

    Real exports mix ISO dates, US (MM/DD/YYYY) and non-US (DD/MM/YYYY)
    orderings, and raw Excel serial numbers. Pandas' default month-first
    reading silently mangles day-first files (03/06/2026 becomes March 6), so
    both interpretations are tried and the one that parses MORE values wins —
    a day > 12 anywhere in the column proves day-first, because those rows
    only parse under that reading. Ties prefer day-first (DD/MM dominates
    non-US POS systems, and this app formats INR currency).
    """
    raw = pd.Series(series)
    text_values = raw.astype(str).str.strip()

    month_first = _to_datetime(text_values, dayfirst=False)
    day_first = _to_datetime(text_values, dayfirst=True)

    # Year-first values (ISO "2026-06-10") are unambiguous, and pandas'
    # dayfirst=True actively misreads them (June 10 becomes October 6), so a
    # mostly year-first column always takes the month-first parse.
    year_first_ratio = text_values.str.match(r"\d{4}[-/.]").mean()
    if year_first_ratio >= 0.5:
        parsed = month_first
    elif day_first.notna().sum() >= month_first.notna().sum():
        parsed = day_first
    else:
        parsed = month_first

    # Excel serial day numbers (e.g. 46081 == 2026-03-01). Only plausible
    # modern values are converted so ordinary IDs aren't misread as dates.
    numeric = pd.to_numeric(raw, errors="coerce")
    serial_mask = numeric.between(20_000, 80_000) & parsed.isna()  # ~1954..2119
    if serial_mask.any():
        parsed = parsed.copy()
        parsed[serial_mask] = pd.to_datetime(
            numeric[serial_mask], unit="D", origin="1899-12-30", errors="coerce"
        )

    return parsed.dt.date


def _to_datetime(values: pd.Series, dayfirst: bool) -> pd.Series:
    text_values = values.astype(str).str.strip()
    try:
        # format="mixed" parses each element independently, so one odd row
        # can't force the whole column to NaT.
        return pd.to_datetime(text_values, errors="coerce", dayfirst=dayfirst, format="mixed")
    except (TypeError, ValueError):
        return pd.to_datetime(text_values, errors="coerce", dayfirst=dayfirst)


def _map_columns(df: pd.DataFrame) -> dict[str, str]:
    columns = list(df.columns)
    mapped: dict[str, str] = {}

    for target in ("item_name", "quantity", "unit_cost", "date"):
        column = _best_keyword_column(columns, HEADER_KEYWORDS[target])
        if column:
            mapped[target] = column

    revenue_column = _best_keyword_column(
        columns,
        [alias for alias in HEADER_KEYWORDS["revenue"] if alias not in {"price"}],
        exclude={mapped.get("quantity"), mapped.get("unit_cost")},
    )
    if revenue_column:
        mapped["revenue"] = revenue_column

    price_column = _best_keyword_column(columns, ["unitprice", "price", "rate"], exclude=set(mapped.values()))
    if price_column:
        mapped["unit_price"] = price_column

    if "item_name" not in mapped:
        mapped["item_name"] = _best_text_column(df)

    numeric_columns = [
        col for col in columns if col != mapped.get("item_name") and _to_number(df[col]).notna().any()
    ]
    if "quantity" not in mapped and numeric_columns:
        mapped["quantity"] = min(numeric_columns, key=lambda col: _to_number(df[col]).median(skipna=True) or 0)

    if "revenue" not in mapped and numeric_columns:
        excluded = {mapped.get("quantity"), mapped.get("unit_cost")}
        candidates = [col for col in numeric_columns if col not in excluded]
        if candidates:
            mapped["revenue"] = max(candidates, key=lambda col: _to_number(df[col]).sum(skipna=True))

    return mapped


def _best_keyword_column(columns: list[str], aliases: list[str], exclude: set[str | None] | None = None):
    exclude = exclude or set()
    scored = []
    for col in columns:
        if col in exclude:
            continue
        score = sum(1 for alias in aliases if alias in col)
        if score:
            scored.append((score, len(col), col))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][2]


def _best_text_column(df: pd.DataFrame) -> str:
    scores = []
    for col in df.columns:
        series = df[col].dropna().astype(str)
        if series.empty:
            continue
        numeric_ratio = _to_number(series).notna().mean()
        average_length = series.map(len).mean()
        unique_ratio = series.nunique() / max(len(series), 1)
        scores.append((numeric_ratio, -average_length, -unique_ratio, col))
    if not scores:
        return df.columns[0]
    return sorted(scores, key=lambda item: (item[0], item[1], item[2]))[0][3]


def _to_number(series) -> pd.Series:
    return pd.to_numeric(
        pd.Series(series)
        .astype(str)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .replace({"": None, "-": None, ".": None}),
        errors="coerce",
    )


def _normalize_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9#]+", "", str(value).strip().lower())
