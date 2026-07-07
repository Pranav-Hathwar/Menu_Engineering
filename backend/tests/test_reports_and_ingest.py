"""Tests for monthly reports, the 2-month retention policy, and email ingestion."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

import datetime as dt
from email.message import EmailMessage

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.sales import SalesData
from app.models.upload_batch import UploadBatch
from app.models.user import User
from app.services.email_ingest_service import extract_report_attachments, ingest_email_message
from app.services.report_service import (
    get_monthly_report,
    get_retention_status,
    list_available_months,
    purge_old_months,
    retention_cutoff,
)


def make_factory():
    """Session factory over ONE shared in-memory DB (ingestion opens its own session)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def make_session():
    factory = make_factory()
    db = factory()
    user = User(email="owner@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user, factory


def add_sale(db, owner_id, day, item="Dosa", qty=2, revenue=200.0, cost=40.0, batch=None):
    db.add(
        SalesData(
            restaurant_name="Mint Masala", item_name=item, quantity=qty,
            revenue=revenue, unit_cost=cost, date=day, owner_id=owner_id,
            upload_batch_id=batch,
        )
    )
    db.commit()


# ---------------------------------------------------------------- monthly report

def test_monthly_report_for_a_full_past_month():
    db, user, _ = make_session()
    add_sale(db, user.id, dt.date(2026, 5, 3), item="Dosa", qty=4, revenue=400.0, cost=40.0)
    add_sale(db, user.id, dt.date(2026, 5, 20), item="Coffee", qty=10, revenue=300.0, cost=12.0)
    add_sale(db, user.id, dt.date(2026, 6, 1), item="Dosa")  # outside May

    report = get_monthly_report(db, owner_id=user.id, restaurant_name="Mint Masala", month_key="2026-05")
    summary = report["summary"]

    assert summary["label"] == "May 2026"
    assert summary["is_partial"] is False
    assert summary["days_recorded"] == 2
    assert summary["total_revenue"] == 700.0
    # 400 - 4*40 + 300 - 10*12 = 240 + 180
    assert summary["total_profit"] == pytest.approx(420.0)
    assert summary["top_item"] == "Dosa"
    assert summary["best_day"]["date"] == dt.date(2026, 5, 3)
    assert {i["item_name"] for i in report["items"]} == {"Dosa", "Coffee"}


def test_monthly_report_current_month_is_month_to_date():
    db, user, _ = make_session()
    today = dt.date.today()
    add_sale(db, user.id, today.replace(day=1))

    report = get_monthly_report(db, owner_id=user.id, restaurant_name="Mint Masala")
    summary = report["summary"]

    assert summary["month"] == today.strftime("%Y-%m")
    assert summary["start_date"] == today.replace(day=1)
    assert summary["end_date"] == today
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    assert summary["is_partial"] == (today.day < last_day)


def test_monthly_report_rejects_bad_month_key():
    db, user, _ = make_session()
    with pytest.raises(HTTPException) as exc:
        get_monthly_report(db, owner_id=user.id, month_key="june-2026")
    assert exc.value.status_code == 400


def test_list_available_months_newest_first():
    db, user, _ = make_session()
    add_sale(db, user.id, dt.date(2026, 5, 3))
    add_sale(db, user.id, dt.date(2026, 7, 1))
    add_sale(db, user.id, dt.date(2026, 7, 2))

    assert list_available_months(db, owner_id=user.id) == ["2026-07", "2026-05"]


# ---------------------------------------------------------------- retention

def test_retention_keeps_current_and_previous_month_only():
    db, user, _ = make_session()
    today = dt.date.today()
    cutoff = retention_cutoff(today)
    old_day = cutoff - dt.timedelta(days=10)       # two months ago -> old
    previous_day = cutoff                           # previous month -> keep
    add_sale(db, user.id, old_day, batch="old-batch")
    db.add(UploadBatch(batch_id="old-batch", owner_id=user.id, restaurant_name="Mint Masala",
                       filename="old.csv", content_hash="h1", row_count=1, total_revenue=200.0))
    add_sale(db, user.id, previous_day, batch="keep-batch")
    db.add(UploadBatch(batch_id="keep-batch", owner_id=user.id, restaurant_name="Mint Masala",
                       filename="keep.csv", content_hash="h2", row_count=1, total_revenue=200.0))
    add_sale(db, user.id, today)
    db.commit()

    status = get_retention_status(db, owner_id=user.id)
    assert status["cleanup_due"] is True
    assert status["old_rows"] == 1
    assert status["old_months"] == [old_day.strftime("%Y-%m")]

    result = purge_old_months(db, owner_id=user.id)
    assert result["rows_deleted"] == 1
    assert result["batches_removed"] == 1  # the emptied old batch is cleaned up

    remaining = {row.date for row in db.query(SalesData).all()}
    assert remaining == {previous_day, today}
    assert {b.batch_id for b in db.query(UploadBatch).all()} == {"keep-batch"}
    assert get_retention_status(db, owner_id=user.id)["cleanup_due"] is False


# ---------------------------------------------------------------- email ingestion

def build_report_email(sender="pos@mintmasala.com", filename="daily_report.csv",
                       body=b"Item,Qty,Revenue,Cost,Date\nDosa,5,500,100,2026-07-06\n"):
    message = EmailMessage()
    message["From"] = f"Mint Masala POS <{sender}>"
    message["To"] = "reports@menumind.test"
    message["Subject"] = "Daily Sales Report"
    message.set_content("Attached is today's report.")
    message.add_attachment(body, maintype="text", subtype="csv", filename=filename)
    return message


def test_extract_report_attachments_filters_by_extension():
    message = build_report_email(filename="report.csv")
    message.add_attachment(b"binary", maintype="image", subtype="png", filename="logo.png")

    attachments = extract_report_attachments(message)
    assert [name for name, _ in attachments] == ["report.csv"]


def test_ingest_email_message_stores_sales_and_skips_duplicates():
    db, user, factory = make_session()

    outcome = ingest_email_message(build_report_email(), session_factory=factory)
    assert outcome["ingested"] == 1 and outcome["failed"] == 0

    check = factory()
    rows = check.query(SalesData).all()
    assert len(rows) == 1
    assert rows[0].restaurant_name == "Mint Masala"
    assert rows[0].item_name == "Dosa"
    assert rows[0].date == dt.date(2026, 7, 6)
    check.close()

    # The same report arriving again must be skipped, not double-counted.
    outcome = ingest_email_message(build_report_email(), session_factory=factory)
    assert outcome["ingested"] == 0 and outcome["skipped"] == 1

    check = factory()
    assert check.query(SalesData).count() == 1
    check.close()


def test_ingest_email_message_respects_sender_allowlist(monkeypatch):
    from app.config import settings
    db, user, factory = make_session()
    monkeypatch.setattr(settings, "INGEST_ALLOWED_SENDERS", "pos@mintmasala.com")

    blocked = ingest_email_message(build_report_email(sender="spam@evil.com"), session_factory=factory)
    assert blocked["ingested"] == 0
    assert "not in INGEST_ALLOWED_SENDERS" in blocked["details"][0]

    allowed = ingest_email_message(build_report_email(sender="pos@mintmasala.com"), session_factory=factory)
    assert allowed["ingested"] == 1
