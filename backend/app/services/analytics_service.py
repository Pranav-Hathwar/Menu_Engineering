"""Aggregated analytics and menu-engineering calculations."""

from datetime import date, timedelta
from statistics import median
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales import SalesData
from app.services.recipe_service import get_recipe_costs

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
    ``date``; grouping by that column yields one total per calendar day. Rows
    are grouped by (date, item) first so that items with a defined recipe use
    their recipe cost instead of the flat uploaded ``unit_cost``. Returns rows
    ordered newest-first; the frontend offers re-sorting.
    """
    query = db.query(
        SalesData.date,
        SalesData.item_name,
        func.sum(SalesData.revenue).label("total_revenue"),
        func.sum(SalesData.quantity).label("total_quantity"),
        func.sum(SalesData.unit_cost * SalesData.quantity).label("total_cost"),
        func.count(SalesData.id).label("line_items"),
    )
    query = _apply_filters(query, owner_id, restaurant_name, start_date, end_date)
    results = query.group_by(SalesData.date, SalesData.item_name).all()

    recipe_costs = get_recipe_costs(db, owner_id, restaurant_name)

    buckets: dict = {}
    for row in results:
        if row.date is None:
            continue
        qty = int(row.total_quantity or 0)
        if row.item_name in recipe_costs:
            cost = recipe_costs[row.item_name] * qty
        else:
            cost = row.total_cost or 0.0
        bucket = buckets.setdefault(
            row.date, {"revenue": 0.0, "quantity": 0, "cost": 0.0, "line_items": 0}
        )
        bucket["revenue"] += row.total_revenue or 0.0
        bucket["quantity"] += qty
        bucket["cost"] += cost
        bucket["line_items"] += int(row.line_items or 0)

    return [
        {
            "date": day,
            "total_revenue": bucket["revenue"],
            "total_quantity": bucket["quantity"],
            "total_profit": bucket["revenue"] - bucket["cost"],
            "line_items": bucket["line_items"],
        }
        for day, bucket in sorted(buckets.items(), reverse=True)
    ]


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

    # Items with a defined recipe use their live bill-of-materials cost, so
    # margins track today's ingredient prices rather than upload-time values.
    recipe_costs = get_recipe_costs(db, owner_id, restaurant_name)

    valid_items = []

    for row in results:
        qty = row.total_quantity or 0
        rev = row.total_revenue or 0.0
        if not row.item_name or qty <= 0 or rev <= 0:
            continue

        if row.item_name in recipe_costs:
            avg_unit_cost = recipe_costs[row.item_name]
            cogs = avg_unit_cost * qty
            cost_source = "recipe"
        else:
            cogs = row.total_cost or 0.0
            avg_unit_cost = cogs / qty
            cost_source = "upload"

        avg_unit_revenue = rev / qty
        profit_per_unit = avg_unit_revenue - avg_unit_cost
        total_profit = rev - cogs

        valid_items.append(
            {
                "item_name": row.item_name,
                "total_quantity": qty,
                "total_revenue": rev,
                "unit_cost": avg_unit_cost,
                "profit": profit_per_unit,
                "total_profit": total_profit,
                # Gross margin as a % of revenue; rev > 0 is guaranteed above.
                "profit_margin": (total_profit / rev) * 100.0,
                "cost_source": cost_source,
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

    # Compare average daily revenue between the first and second half of the
    # period. Comparing only the first vs last single day (the old approach)
    # made the trend hostage to two arbitrary days' noise.
    trend = "stable"
    if len(daily) >= 2:
        midpoint = len(daily) // 2
        first_half = [d.revenue or 0 for d in daily[:midpoint]]
        second_half = [d.revenue or 0 for d in daily[midpoint:]]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        if second_avg > first_avg * 1.1:
            trend = "up"
        elif second_avg < first_avg * 0.9:
            trend = "down"

    # Pareto concentration: how few items drive 80% of revenue.
    by_revenue = sorted(classifications, key=lambda item: item["total_revenue"], reverse=True)
    cumulative = 0.0
    items_to_80 = len(by_revenue)
    for idx, item in enumerate(by_revenue, start=1):
        cumulative += item["total_revenue"]
        if total_revenue > 0 and cumulative >= total_revenue * 0.8:
            items_to_80 = idx
            break
    pareto_pct = (items_to_80 / len(by_revenue)) * 100 if by_revenue else 0.0

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
            "title": "Revenue concentration risk",
            "value": f"{items_to_80} of {len(by_revenue)} items drive 80% of revenue",
            "detail": (
                f"{pareto_pct:.0f}% of the menu generates 80% of revenue. "
                "A highly concentrated menu is efficient but fragile — protect those items' quality and supply."
            ),
            "severity": "warning" if pareto_pct <= 25 else "neutral",
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


WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Rolling window for the smoothed revenue line and the period comparison.
TREND_WINDOW_DAYS = 7


def get_sales_trends(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Time-based analytics: smoothed daily series, weekday profile,
    Pareto revenue concentration, and a last-week-vs-prior-week comparison.

    The moving average is computed over the last N *observed* days rather than
    calendar days, so sparse data (e.g. a restaurant closed on Mondays) still
    yields a meaningful smoothed line.
    """
    daily = get_daily_sales(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start_date, end_date=end_date
    )
    daily = sorted(daily, key=lambda row: row["date"])

    # --- Smoothed daily series -------------------------------------------
    series = []
    for idx, row in enumerate(daily):
        window = daily[max(0, idx - TREND_WINDOW_DAYS + 1) : idx + 1]
        ma_revenue = sum(d["total_revenue"] for d in window) / len(window)
        series.append(
            {
                "date": row["date"],
                "total_revenue": round(row["total_revenue"], 2),
                "total_profit": round(row["total_profit"], 2),
                "total_quantity": row["total_quantity"],
                "ma_revenue": round(ma_revenue, 2),
            }
        )

    # --- Weekday profile ---------------------------------------------------
    weekday_buckets: dict[int, dict[str, float]] = {}
    for row in daily:
        bucket = weekday_buckets.setdefault(row["date"].weekday(), {"revenue": 0.0, "quantity": 0, "days": 0})
        bucket["revenue"] += row["total_revenue"]
        bucket["quantity"] += row["total_quantity"]
        bucket["days"] += 1

    weekday = [
        {
            "weekday": WEEKDAY_NAMES[day_index],
            "avg_revenue": round(bucket["revenue"] / bucket["days"], 2),
            "avg_quantity": round(bucket["quantity"] / bucket["days"], 1),
            "days_observed": int(bucket["days"]),
        }
        for day_index, bucket in sorted(weekday_buckets.items())
    ]

    # --- Pareto: which items concentrate revenue ---------------------------
    summary = get_sales_summary(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start_date, end_date=end_date
    )
    total_revenue = sum(item["total_revenue"] for item in summary)
    pareto = []
    cumulative = 0.0
    for item in sorted(summary, key=lambda entry: entry["total_revenue"], reverse=True):
        cumulative += item["total_revenue"]
        pareto.append(
            {
                "item_name": item["item_name"],
                "total_revenue": round(item["total_revenue"], 2),
                "revenue_share": round((item["total_revenue"] / total_revenue) * 100, 2) if total_revenue else 0.0,
                "cumulative_share": round((cumulative / total_revenue) * 100, 2) if total_revenue else 0.0,
            }
        )

    return {
        "daily": series,
        "weekday": weekday,
        "pareto": pareto[:15],
        "comparison": _period_comparison(daily),
    }


def _period_comparison(daily_ascending: list[dict]) -> Optional[dict]:
    """Compare the most recent 7 calendar days against the 7 days before them.

    Anchored on the newest date present in the data (not "today"), so an
    upload of last month's sales still produces a sensible comparison.
    """
    if len(daily_ascending) < 2:
        return None

    anchor = daily_ascending[-1]["date"]
    current_start = anchor - timedelta(days=TREND_WINDOW_DAYS - 1)
    previous_start = current_start - timedelta(days=TREND_WINDOW_DAYS)

    current = [d for d in daily_ascending if d["date"] >= current_start]
    previous = [d for d in daily_ascending if previous_start <= d["date"] < current_start]
    if not previous:
        return None

    def totals(rows):
        return (
            sum(r["total_revenue"] for r in rows),
            sum(r["total_profit"] for r in rows),
            sum(r["total_quantity"] for r in rows),
        )

    current_revenue, current_profit, current_units = totals(current)
    previous_revenue, previous_profit, previous_units = totals(previous)

    def change_pct(now, before):
        if before == 0:
            return None
        return round(((now - before) / abs(before)) * 100, 2)

    return {
        "window_days": TREND_WINDOW_DAYS,
        "current_start": current_start,
        "current_end": anchor,
        "previous_start": previous_start,
        "previous_end": current_start - timedelta(days=1),
        "current_revenue": round(current_revenue, 2),
        "previous_revenue": round(previous_revenue, 2),
        "revenue_change_pct": change_pct(current_revenue, previous_revenue),
        "current_profit": round(current_profit, 2),
        "previous_profit": round(previous_profit, 2),
        "profit_change_pct": change_pct(current_profit, previous_profit),
        "current_units": int(current_units),
        "previous_units": int(previous_units),
        "units_change_pct": change_pct(current_units, previous_units),
    }
