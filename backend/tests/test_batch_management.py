import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.sales import SalesData
from app.models.user import User
from app.services.upload_service import (
    delete_upload_batch,
    list_upload_batches,
    process_upload,
)

PAYLOAD = b"Item Name,Quantity,Revenue,Cost,Date\nBurger,5,500,120,2026-01-01\nFries,10,300,40,2026-01-01"


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


def test_identical_reupload_is_rejected():
    db, user = make_session()
    process_upload(PAYLOAD, "sales.csv", db, "Kitchen", owner_id=user.id)

    with pytest.raises(HTTPException) as exc:
        process_upload(PAYLOAD, "sales.csv", db, "Kitchen", owner_id=user.id)
    assert exc.value.status_code == 409

    # No double-counting occurred.
    assert db.query(SalesData).filter(SalesData.owner_id == user.id).count() == 2


def test_allow_duplicate_override_lets_it_through():
    db, user = make_session()
    process_upload(PAYLOAD, "sales.csv", db, "Kitchen", owner_id=user.id)
    process_upload(PAYLOAD, "sales.csv", db, "Kitchen", owner_id=user.id, allow_duplicate=True)
    assert db.query(SalesData).filter(SalesData.owner_id == user.id).count() == 4
    assert len(list_upload_batches(db, owner_id=user.id)) == 2


def test_same_file_different_restaurant_allowed():
    db, user = make_session()
    process_upload(PAYLOAD, "sales.csv", db, "Kitchen A", owner_id=user.id)
    # Same bytes, different restaurant → not a duplicate.
    process_upload(PAYLOAD, "sales.csv", db, "Kitchen B", owner_id=user.id)
    assert {b["restaurant_name"] for b in list_upload_batches(db, owner_id=user.id)} == {"Kitchen A", "Kitchen B"}


def test_delete_batch_removes_only_its_rows():
    db, user = make_session()
    r1 = process_upload(PAYLOAD, "a.csv", db, "Kitchen", owner_id=user.id)
    other = b"Item Name,Quantity,Revenue,Cost,Date\nSoda,3,90,20,2026-01-02"
    process_upload(other, "b.csv", db, "Kitchen", owner_id=user.id)

    deleted = delete_upload_batch(db, owner_id=user.id, batch_id=r1["upload_batch_id"])
    assert deleted == 2
    remaining = db.query(SalesData).filter(SalesData.owner_id == user.id).all()
    assert {row.item_name for row in remaining} == {"Soda"}
    assert len(list_upload_batches(db, owner_id=user.id)) == 1


def test_delete_unknown_batch_404():
    db, user = make_session()
    with pytest.raises(HTTPException) as exc:
        delete_upload_batch(db, owner_id=user.id, batch_id="does-not-exist")
    assert exc.value.status_code == 404


def test_delete_is_owner_scoped():
    db, user = make_session()
    other = User(email="other@example.com", hashed_password="hash")
    db.add(other)
    db.commit()
    db.refresh(other)

    result = process_upload(PAYLOAD, "sales.csv", db, "Kitchen", owner_id=user.id)
    # A different owner cannot delete this batch.
    with pytest.raises(HTTPException) as exc:
        delete_upload_batch(db, owner_id=other.id, batch_id=result["upload_batch_id"])
    assert exc.value.status_code == 404
    assert db.query(SalesData).filter(SalesData.owner_id == user.id).count() == 2
