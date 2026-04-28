"""File ingestion pipeline for messy restaurant sales exports."""

from __future__ import annotations

import datetime as dt
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
):
    dataframe = _read_dataframe(file_bytes, filename)
    dataframe = _discover_headers(dataframe)
    dataframe = _normalize_columns(dataframe)
    records, metadata = _normalize_sales_records(dataframe)

    if not records:
        raise HTTPException(
            status_code=400,
            detail="The file was readable, but no valid sales rows with item and revenue could be extracted.",
        )

    batch_id = str(uuid.uuid4())
    sales_objects = [
        SalesData(
            **record,
            restaurant_name=restaurant_name.strip(),
            owner_id=owner_id,
            upload_batch_id=batch_id,
        )
        for record in records
    ]

    db.add_all(sales_objects)
    db.commit()

    total_revenue = sum(record["revenue"] for record in records)
    total_units = sum(record["quantity"] for record in records)
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
    }


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
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(
                io.BytesIO(file_bytes),
                sep=None,
                engine="python",
                encoding=encoding,
                skip_blank_lines=True,
            )
        except Exception as exc:
            last_error = exc

    try:
        return pd.read_csv(io.BytesIO(file_bytes), encoding="latin1", skip_blank_lines=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CSV parsing failed: {last_error or exc}") from exc


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


def _normalize_sales_records(df: pd.DataFrame):
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
        working["date"] = pd.to_datetime(df[date_source], errors="coerce").dt.date
    else:
        working["date"] = dt.date.today()

    today = dt.date.today()
    working["item_name"] = working["item_name"].str.replace(r"\s+", " ", regex=True).str.title()
    working["quantity"] = working["quantity"].fillna(1).clip(lower=0).round().astype(int)
    working["revenue"] = working["revenue"].fillna(0.0).clip(lower=0).astype(float)
    working["unit_cost"] = working["unit_cost"].fillna(0.0).clip(lower=0).astype(float)
    working["date"] = working["date"].apply(lambda value: value if pd.notna(value) else today)

    initial_rows = len(working)
    valid = working[
        working["item_name"].map(lambda value: _normalize_token(value) not in JUNK_ITEM_NAMES)
        & (working["revenue"] > 0)
        & (working["quantity"] > 0)
    ]

    records = valid[["item_name", "quantity", "revenue", "unit_cost", "date"]].to_dict(orient="records")
    return records, {"rows_rejected": initial_rows - len(records), "detected_columns": mapped}


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
