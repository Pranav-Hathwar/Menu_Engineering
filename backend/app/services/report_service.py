"""Monthly reports and the two-month data-retention policy.

Retention policy: the database keeps the CURRENT month and the PREVIOUS month.
Anything older is flagged to the owner, who must explicitly confirm deletion —
nothing is ever removed automatically.
"""

import calendar
import re
from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.sales import SalesData
from app.models.upload_batch import UploadBatch
from app.services.analytics_service import get_daily_sales, get_menu_engineering_classification

MONTH_KEY_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


# --------------------------------------------------------------------------
# Monthly report
# --------------------------------------------------------------------------

def get_monthly_report(
    db: Session,
    owner_id: int,
    restaurant_name: Optional[str] = None,
    month_key: Optional[str] = None,
):
    """Item-wise report for one calendar month.

    ``month_key`` is "YYYY-MM"; omitted means the current month. For the
    current month the report covers the 1st through *today* (month-to-date)
    and is marked ``is_partial`` so the UI can label it clearly.
    """
    today = date.today()
    if month_key:
        match = MONTH_KEY_PATTERN.match(month_key.strip())
        if not match:
            raise HTTPException(status_code=400, detail="month must look like 2026-07 (YYYY-MM).")
        year, month = int(match.group(1)), int(match.group(2))
    else:
        year, month = today.year, today.month

    start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    is_current = (year, month) == (today.year, today.month)
    end = min(month_end, today) if is_current else month_end
    is_partial = is_current and today < month_end

    items = get_menu_engineering_classification(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start, end_date=end
    )
    items = sorted(items, key=lambda item: item["total_revenue"], reverse=True)
    daily = get_daily_sales(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start, end_date=end
    )

    best_day = max(daily, key=lambda d: d["total_revenue"], default=None)
    top_item = items[0]["item_name"] if items else None

    return {
        "summary": {
            "month": f"{year:04d}-{month:02d}",
            "label": start.strftime("%B %Y"),
            "start_date": start,
            "end_date": end,
            "is_partial": is_partial,
            "days_recorded": len(daily),
            "total_revenue": round(sum(i["total_revenue"] for i in items), 2),
            "total_profit": round(sum(i["total_profit"] for i in items), 2),
            "total_units": int(sum(i["total_quantity"] for i in items)),
            "item_count": len(items),
            "best_day": best_day,
            "top_item": top_item,
        },
        "items": items,
        "daily": daily,
    }


def list_available_months(db: Session, owner_id: int, restaurant_name: Optional[str] = None):
    """Distinct months (newest first) that have sales data, as YYYY-MM keys."""
    query = db.query(SalesData.date).filter(SalesData.owner_id == owner_id)
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)
    dates = {row[0] for row in query.distinct().all() if row[0]}
    return sorted({d.strftime("%Y-%m") for d in dates}, reverse=True)


# --------------------------------------------------------------------------
# Retention (keep current + previous month; older data needs owner sign-off)
# --------------------------------------------------------------------------

def retention_cutoff(today: Optional[date] = None) -> date:
    """First day of the previous month — anything before it is 'old'."""
    today = today or date.today()
    first_of_this_month = today.replace(day=1)
    return (first_of_this_month - timedelta(days=1)).replace(day=1)


def get_retention_status(db: Session, owner_id: int):
    cutoff = retention_cutoff()
    old_dates = {
        row[0]
        for row in db.query(SalesData.date)
        .filter(SalesData.owner_id == owner_id, SalesData.date < cutoff)
        .distinct()
        .all()
        if row[0]
    }
    old_rows = (
        db.query(SalesData)
        .filter(SalesData.owner_id == owner_id, SalesData.date < cutoff)
        .count()
    )
    return {
        "cutoff": cutoff,
        "old_rows": old_rows,
        "old_months": sorted({d.strftime("%Y-%m") for d in old_dates}),
        "cleanup_due": old_rows > 0,
    }


def purge_old_months(db: Session, owner_id: int):
    """Delete sales older than the previous month. Owner-confirmed only —
    the API endpoint behind this is called from an explicit OK dialog."""
    cutoff = retention_cutoff()
    rows_deleted = (
        db.query(SalesData)
        .filter(SalesData.owner_id == owner_id, SalesData.date < cutoff)
        .delete(synchronize_session=False)
    )

    # Upload batches whose rows are all gone are just clutter — remove them.
    remaining_batches = (
        db.query(SalesData.upload_batch_id)
        .filter(SalesData.owner_id == owner_id, SalesData.upload_batch_id.isnot(None))
        .distinct()
    )
    batches_removed = (
        db.query(UploadBatch)
        .filter(UploadBatch.owner_id == owner_id, ~UploadBatch.batch_id.in_(remaining_batches))
        .delete(synchronize_session=False)
    )
    db.commit()
    return {
        "rows_deleted": int(rows_deleted),
        "batches_removed": int(batches_removed),
        "cutoff": cutoff,
        "message": f"Removed {rows_deleted} sales row(s) older than {cutoff.strftime('%B %Y')}.",
    }
