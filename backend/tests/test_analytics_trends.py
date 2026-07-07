"""Tests for trend analytics, period comparison, and classification metrics."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.sales import SalesData
from app.models.user import User
from app.services.analytics_service import (
    get_business_insights,
    get_menu_engineering_classification,
    get_sales_trends,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    user = User(email="owner@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user


def seed_daily_sales(db, owner_id, days, revenue_per_day=100.0, start=dt.date(2026, 6, 1)):
    for offset in range(days):
        db.add(
            SalesData(
                restaurant_name="Trend Cafe",
                item_name="Coffee",
                quantity=2,
                revenue=revenue_per_day,
                unit_cost=10.0,
                date=start + dt.timedelta(days=offset),
                owner_id=owner_id,
            )
        )
    db.commit()


def test_trends_moving_average_smooths_series():
    db, user = make_session()
    # 10 days at Rs 100/day, then a 1-day spike to Rs 1100.
    seed_daily_sales(db, user.id, days=10, revenue_per_day=100.0)
    db.add(
        SalesData(
            restaurant_name="Trend Cafe", item_name="Coffee", quantity=2,
            revenue=1000.0, unit_cost=10.0, date=dt.date(2026, 6, 10), owner_id=user.id,
        )
    )
    db.commit()

    trends = get_sales_trends(db, owner_id=user.id, restaurant_name="Trend Cafe")
    series = trends["daily"]

    assert [point["date"] for point in series] == sorted(point["date"] for point in series)
    last = series[-1]
    assert last["total_revenue"] == 1100.0
    # 7-day window: six Rs-100 days + the Rs-1100 day = 1700 / 7
    assert abs(last["ma_revenue"] - (600 + 1100) / 7) < 0.01


def test_trends_weekday_profile_and_pareto_shares():
    db, user = make_session()
    # 2026-06-01 is a Monday; 14 days = every weekday observed twice.
    seed_daily_sales(db, user.id, days=14, revenue_per_day=100.0)
    db.add(
        SalesData(
            restaurant_name="Trend Cafe", item_name="Biryani", quantity=1,
            revenue=300.0, unit_cost=100.0, date=dt.date(2026, 6, 1), owner_id=user.id,
        )
    )
    db.commit()

    trends = get_sales_trends(db, owner_id=user.id, restaurant_name="Trend Cafe")

    weekday = {row["weekday"]: row for row in trends["weekday"]}
    assert set(weekday) == {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
    assert weekday["Monday"]["days_observed"] == 2
    # Mondays: (100 + 300 + 100) / 2
    assert abs(weekday["Monday"]["avg_revenue"] - 250.0) < 0.01
    assert abs(weekday["Tuesday"]["avg_revenue"] - 100.0) < 0.01

    pareto = trends["pareto"]
    assert pareto[0]["item_name"] == "Coffee"  # 1400 of 1700 total
    assert abs(pareto[0]["revenue_share"] - (1400 / 1700) * 100) < 0.1
    assert abs(pareto[-1]["cumulative_share"] - 100.0) < 0.01


def test_trends_period_comparison_detects_growth():
    db, user = make_session()
    # Prior week Rs 100/day, latest week Rs 200/day.
    seed_daily_sales(db, user.id, days=7, revenue_per_day=100.0, start=dt.date(2026, 6, 1))
    seed_daily_sales(db, user.id, days=7, revenue_per_day=200.0, start=dt.date(2026, 6, 8))

    trends = get_sales_trends(db, owner_id=user.id, restaurant_name="Trend Cafe")
    comparison = trends["comparison"]

    assert comparison is not None
    assert comparison["current_revenue"] == 1400.0
    assert comparison["previous_revenue"] == 700.0
    assert comparison["revenue_change_pct"] == 100.0
    assert comparison["current_start"] == dt.date(2026, 6, 8)
    assert comparison["previous_end"] == dt.date(2026, 6, 7)


def test_classification_includes_margin_metrics():
    db, user = make_session()
    for _ in range(3):
        db.add(
            SalesData(
                restaurant_name="Margin Diner", item_name="Thali", quantity=2,
                revenue=400.0, unit_cost=50.0, date=dt.date(2026, 6, 1), owner_id=user.id,
            )
        )
    db.commit()

    items = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Margin Diner")
    thali = items[0]

    # 6 units, Rs 1200 revenue, Rs 300 COGS.
    assert thali["total_profit"] == 900.0
    assert abs(thali["profit_margin"] - 75.0) < 0.01
    assert abs(thali["profit"] - 150.0) < 0.01


def test_insights_include_pareto_and_half_period_trend():
    db, user = make_session()
    # First half flat Rs 100/day, second half Rs 300/day: trend must be "up".
    seed_daily_sales(db, user.id, days=5, revenue_per_day=100.0, start=dt.date(2026, 6, 1))
    seed_daily_sales(db, user.id, days=5, revenue_per_day=300.0, start=dt.date(2026, 6, 6))

    insights = get_business_insights(db, owner_id=user.id, restaurant_name="Trend Cafe")
    by_title = {insight["title"]: insight for insight in insights}

    assert by_title["Sales trend"]["value"] == "up"
    assert "Revenue concentration risk" in by_title


def test_combo_items_identified_and_excluded_from_thresholds():
    from app.services.analytics_service import is_combo_item

    assert is_combo_item("Tdh")
    assert is_combo_item("TDH Special")
    assert is_combo_item("Veg Buffet Lunch")
    assert is_combo_item("Family Combo Meal")
    assert not is_combo_item("Masala Dosa")
    assert not is_combo_item("Tandoori Roti")  # 'tdh' must match as a word, not a substring

    db, user = make_session()
    # A huge-profit TDH buffet plus modest a-la-carte items. Without the combo
    # exclusion, TDH's Rs 400 unit profit would drag the profitability median
    # up and turn ordinary dishes into false Dogs/Plowhorses.
    for item, qty, revenue, cost in [
        ("Tdh", 27, 15900.0, 500.0),
        ("Dosa", 10, 1000.0, 40.0),
        ("Idli", 12, 600.0, 20.0),
        ("Coffee", 30, 900.0, 10.0),
    ]:
        db.add(SalesData(restaurant_name="Mint", item_name=item, quantity=qty,
                         revenue=revenue, unit_cost=cost, date=dt.date(2025, 7, 30), owner_id=user.id))
    db.commit()

    items = {i["item_name"]: i for i in get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Mint")}

    assert items["Tdh"]["item_type"] == "combo"
    assert items["Dosa"]["item_type"] == "standard"
    # Dosa (profit/unit 60) must classify against a-la-carte medians only —
    # not against the TDH's ~Rs 89/unit profit.
    assert items["Dosa"]["category"] in {"Star", "Plowhorse", "Puzzle"}


def test_combo_items_get_dedicated_recommendation():
    from app.services.recommendation_service import get_recommendations

    db, user = make_session()
    db.add(SalesData(restaurant_name="Mint", item_name="Tdh", quantity=27,
                     revenue=15900.0, unit_cost=500.0, date=dt.date(2025, 7, 30), owner_id=user.id))
    db.commit()

    recs = get_recommendations(db, owner_id=user.id, restaurant_name="Mint")
    tdh = next(r for r in recs if r["item_name"] == "Tdh")
    assert tdh["category"] == "Combo"
    assert "set menu" in tdh["recommendation"].lower() or "buffet" in tdh["recommendation"].lower()
