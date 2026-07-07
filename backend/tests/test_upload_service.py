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


def test_process_upload_parses_dayfirst_dates_correctly():
    db, user = make_session()
    # 13/06/2026 only parses day-first, so the whole column must be read
    # day-first: 03/06/2026 is June 3rd, NOT March 6th.
    payload = (
        b"Item,Qty,Total,Date\n"
        b"Dosa,4,400,03/06/2026\n"
        b"Idli,6,300,13/06/2026\n"
    )

    process_upload(payload, "dayfirst.csv", db, "South Cafe", owner_id=user.id)

    from app.models.sales import SalesData
    import datetime as dt
    dates = {row.date for row in db.query(SalesData).all()}
    assert dates == {dt.date(2026, 6, 3), dt.date(2026, 6, 13)}


def test_process_upload_handles_excel_serial_dates():
    db, user = make_session()
    # 46082 is the Excel serial for 2026-03-01.
    payload = b"Item,Qty,Total,Date\nBurger,2,500,46082\n"

    process_upload(payload, "serial.csv", db, "Serial Diner", owner_id=user.id)

    from app.models.sales import SalesData
    import datetime as dt
    row = db.query(SalesData).first()
    assert row.date == dt.date(2026, 3, 1)


def test_process_upload_defaults_bad_dates_to_file_mode():
    db, user = make_session()
    payload = (
        b"Item,Qty,Total,Date\n"
        b"Pizza,2,500,2026-06-10\n"
        b"Pasta,1,300,2026-06-10\n"
        b"Salad,1,200,not-a-date\n"
    )

    result = process_upload(payload, "mixed.csv", db, "Fallback Bistro", owner_id=user.id)

    from app.models.sales import SalesData
    import datetime as dt
    assert result["dates_defaulted"] == 1
    dates = [row.date for row in db.query(SalesData).all()]
    # The unparseable row inherits the file's most common date, not "today".
    assert dates.count(dt.date(2026, 6, 10)) == 3


def test_dateless_file_uses_filename_date():
    db, user = make_session()
    # No date column anywhere — but the filename carries the report date.
    payload = b"Item Name,Units sold,price,cost\nDosa,3,300,35\nCoffee,10,250,10\n"

    result = process_upload(payload, "Sales_30-07-2025.csv", db, "Mint", owner_id=user.id)

    from app.models.sales import SalesData
    import datetime as dt
    assert result["date_mode"] == "detected"
    assert result["applied_date"] == "2025-07-30"
    assert {row.date for row in db.query(SalesData).all()} == {dt.date(2025, 7, 30)}


def test_dateless_file_uses_title_row_date():
    db, user = make_session()
    payload = (
        b"Daily Sales Report - 30 7 2025,,,\n"
        b"Item Name,Units sold,price,cost\n"
        b"Dosa,3,300,35\n"
    )

    result = process_upload(payload, "sales123.csv", db, "Mint", owner_id=user.id)

    import datetime as dt
    from app.models.sales import SalesData
    assert result["date_mode"] == "detected"
    assert db.query(SalesData).first().date == dt.date(2025, 7, 30)


def test_dateless_file_uses_provided_report_date_over_detection():
    db, user = make_session()
    payload = b"Item Name,Units sold,price,cost\nDosa,3,300,35\n"

    import datetime as dt
    result = process_upload(
        payload, "Sales_01-01-2025.csv", db, "Mint", owner_id=user.id,
        report_date=dt.date(2025, 7, 30),
    )

    from app.models.sales import SalesData
    assert result["date_mode"] == "provided"
    assert db.query(SalesData).first().date == dt.date(2025, 7, 30)


def test_file_with_real_date_column_ignores_report_date():
    db, user = make_session()
    payload = b"Item,Qty,Total,Date\nDosa,3,300,2026-06-10\n"

    import datetime as dt
    result = process_upload(
        payload, "sales.csv", db, "Mint", owner_id=user.id, report_date=dt.date(2025, 7, 30)
    )

    from app.models.sales import SalesData
    assert result["date_mode"] == "column"
    assert db.query(SalesData).first().date == dt.date(2026, 6, 10)
