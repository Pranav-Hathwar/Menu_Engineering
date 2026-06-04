import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.services.analytics_service import get_business_insights, get_menu_engineering_classification
from app.services.upload_service import process_upload


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


def test_process_upload_reads_standard_csv():
    db, user = make_session()
    payload = b"Item Name,Quantity,Revenue,Cost,Date\nBurger,5,500,120,2026-01-01\nFries,10,300,40,2026-01-01"

    result = process_upload(payload, "sales.csv", db, "Test Kitchen", owner_id=user.id)
    classes = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Test Kitchen")

    assert result["rows_ingested"] == 2
    assert result["rows_rejected"] == 0
    assert {item["item_name"] for item in classes} == {"Burger", "Fries"}


def test_process_upload_discovers_headers_after_metadata_rows():
    db, user = make_session()
    payload = b"Report,Generated,Ignored\nStore,North,\nItem,Qty,Total\nPizza,3,900\nPasta,2,500"

    result = process_upload(payload, "messy.csv", db, "North Store", owner_id=user.id)
    classes = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="North Store")

    assert result["rows_ingested"] == 2
    assert sum(item["total_quantity"] for item in classes) == 5


def test_process_upload_reads_json_records_and_generates_insights():
    db, user = make_session()
    payload = b'{"sales":[{"product":"Coffee","units":12,"amount":"1,200","date":"2026-01-02"},{"product":"Tea","units":4,"amount":240,"date":"2026-01-02"}]}'

    result = process_upload(payload, "sales.json", db, "Cafe", owner_id=user.id)
    insights = get_business_insights(db, owner_id=user.id, restaurant_name="Cafe")

    assert result["rows_ingested"] == 2
    assert result["total_units"] == 16
    assert any(insight["title"] == "Revenue concentration" for insight in insights)
