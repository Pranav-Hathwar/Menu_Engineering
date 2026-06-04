"""Aggregated analytics and menu-engineering calculations."""

from datetime import date
from statistics import median
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales import SalesData

# Items selling fewer than this many units over the whole period are too
# sparsely sampled to classify reliably, so they are excluded from the
# threshold math (a single sale should not define a "Puzzle").
MIN_CLASSIFY_QUANTITY = 3


def _apply_filters(
    query,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    if owner_id is not None:
        query = query.filter(SalesData.owner_id == owner_id)
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)
    if start_date:
        query = query.filter(SalesData.date >= start_date)
    if end_date:
        query = query.filter(SalesData.date <= end_date)
    return query


def get_sales_summary(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label("total_quantity"),
        func.sum(SalesData.revenue).label("total_revenue"),
    )
    query = _apply_filters(query, owner_id, restaurant_name, start_date, end_date)
    results = query.group_by(SalesData.item_name).all()

    return [
        {
            "item_name": row.item_name,
            "total_quantity": row.total_quantity or 0,
            "total_revenue": row.total_revenue or 0.0,
        }
        for row in results
        if row.item_name
    ]


def get_daily_sales(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Per-day totals so a monthly upload can be reviewed day by day.

    Even when a whole month is submitted in one file, each row carries its own
    ``date``; grouping by that column yields one total per calendar day. Returns
    rows ordered newest-first; the frontend offers re-sorting.
    """
    query = db.query(
        SalesData.date,
        func.sum(SalesData.revenue).label("total_revenue"),
        func.sum(SalesData.quantity).label("total_quantity"),
        func.sum(SalesData.unit_cost * SalesData.quantity).label("total_cost"),
        func.count(SalesData.id).label("line_items"),
    )
    query = _apply_filters(query, owner_id, restaurant_name, start_date, end_date)
    results = query.group_by(SalesData.date).order_by(SalesData.date.desc()).all()

    daily = []
    for row in results:
        if row.date is None:
            continue
        revenue = row.total_revenue or 0.0
        cost = row.total_cost or 0.0
        daily.append(
            {
                "date": row.date,
                "total_revenue": revenue,
                "total_quantity": int(row.total_quantity or 0),
                "total_profit": revenue - cost,
                "line_items": int(row.line_items or 0),
            }
        )
    return daily


def get_menu_engineering_classification(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label("total_quantity"),
        func.sum(SalesData.revenue).label("total_revenue"),
        func.sum(SalesData.unit_cost * SalesData.quantity).label("total_cost"),
    )
    query = _apply_filters(query, owner_id, restaurant_name, start_date, end_date)
    results = query.group_by(SalesData.item_name).all()

    valid_items = []

    for row in results:
        qty = row.total_quantity or 0
        rev = row.total_revenue or 0.0
        cogs = row.total_cost or 0.0
        if not row.item_name or qty <= 0 or rev <= 0:
            continue

        avg_unit_revenue = rev / qty
        avg_unit_cost = cogs / qty if qty > 0 else 0.0
        profit_per_unit = avg_unit_revenue - avg_unit_cost

        valid_items.append(
            {
                "item_name": row.item_name,
                "total_quantity": qty,
                "total_revenue": rev,
                "unit_cost": avg_unit_cost,
                "profit": profit_per_unit,
                "category": "",
            }
        )

    # Thresholds use the MEDIAN, not the mean: one very-high-margin outlier
    # (e.g. a Rs 750 special) would otherwise drag the mean up and push
    # genuinely profitable items into the wrong quadrant. Sparsely-sampled
    # items are excluded from the threshold population but still classified.
    sample = [i for i in valid_items if i["total_quantity"] >= MIN_CLASSIFY_QUANTITY] or valid_items
    threshold_popularity = median(i["total_quantity"] for i in sample) if sample else 0
    threshold_profitability = median(i["profit"] for i in sample) if sample else 0

    for item in valid_items:
        high_popularity = item["total_quantity"] >= threshold_popularity
        high_profitability = item["profit"] >= threshold_profitability

        if high_popularity and high_profitability:
            item["category"] = "Star"
        elif high_popularity:
            item["category"] = "Plowhorse"
        elif high_profitability:
            item["category"] = "Puzzle"
        else:
            item["category"] = "Dog"

    return valid_items


def get_business_insights(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    classifications = get_menu_engineering_classification(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start_date, end_date=end_date
    )
    if not classifications:
        return []

    total_revenue = sum(item["total_revenue"] for item in classifications)
    total_units = sum(item["total_quantity"] for item in classifications)
    total_profit = sum(item["profit"] * item["total_quantity"] for item in classifications)
    category_counts = {}
    for item in classifications:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

    top_revenue = max(classifications, key=lambda item: item["total_revenue"])
    top_profit = max(classifications, key=lambda item: item["profit"] * item["total_quantity"])
    low_margin = sorted(classifications, key=lambda item: item["profit"])[:3]

    daily_query = db.query(
        SalesData.date,
        func.sum(SalesData.revenue).label("revenue"),
        func.sum(SalesData.quantity).label("quantity"),
    )
    daily_query = _apply_filters(daily_query, owner_id, restaurant_name, start_date, end_date)
    daily = daily_query.group_by(SalesData.date).order_by(SalesData.date.asc()).all()

    trend = "stable"
    if len(daily) >= 2:
        first = daily[0].revenue or 0
        last = daily[-1].revenue or 0
        if last > first * 1.1:
            trend = "up"
        elif last < first * 0.9:
            trend = "down"

    return [
        {
            "title": "Revenue concentration",
            "value": f"{top_revenue['item_name']} leads sales",
            "detail": f"{top_revenue['item_name']} contributes {top_revenue['total_revenue']:.2f} revenue from {top_revenue['total_quantity']} units.",
            "severity": "positive",
        },
        {
            "title": "Profit driver",
            "value": f"{top_profit['item_name']} is the strongest profit contributor",
            "detail": f"Estimated gross profit contribution is {(top_profit['profit'] * top_profit['total_quantity']):.2f}.",
            "severity": "positive",
        },
        {
            "title": "Sales trend",
            "value": trend,
            "detail": f"Observed {len(daily)} sales day(s), {total_units} units, {total_revenue:.2f} revenue, {total_profit:.2f} estimated gross profit.",
            "severity": "warning" if trend == "down" else "positive",
        },
        {
            "title": "Category mix",
            "value": ", ".join(f"{key}: {value}" for key, value in sorted(category_counts.items())),
            "detail": "Use this to rebalance promotion, pricing, and menu placement.",
            "severity": "neutral",
        },
        {
            "title": "Margin watchlist",
            "value": ", ".join(item["item_name"] for item in low_margin),
            "detail": "These items have the weakest estimated per-unit profit and should be reviewed first.",
            "severity": "warning",
        },
    ]
