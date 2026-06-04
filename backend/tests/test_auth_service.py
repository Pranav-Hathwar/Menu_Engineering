import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.user import UserCreate
from app.services.auth_service import authenticate_user, create_user, get_user_by_email
from app.utils.security import verify_password


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return Session()


def test_password_policy_rejects_weak_password():
    with pytest.raises(ValidationError):
        UserCreate(email="owner@example.com", password="password123")


def test_create_user_hashes_password_and_normalizes_email():
    db = make_session()
    user_input = UserCreate(email=" OWNER@Example.COM ", password="StrongPass!123")

    user = create_user(db, user_input)

    assert user.email == "owner@example.com"
    assert user.hashed_password != "StrongPass!123"
    assert verify_password("StrongPass!123", user.hashed_password)
    assert get_user_by_email(db, "OWNER@example.com").id == user.id


def test_create_user_rejects_duplicate_email():
    db = make_session()
    create_user(db, UserCreate(email="owner@example.com", password="StrongPass!123"))

    with pytest.raises(Exception) as exc_info:
        create_user(db, UserCreate(email="OWNER@example.com", password="Another!123"))

    assert getattr(exc_info.value, "status_code", None) == 409


def test_authenticate_user_checks_password_and_active_flag():
    db = make_session()
    user = create_user(db, UserCreate(email="owner@example.com", password="StrongPass!123"))

    assert authenticate_user(db, "owner@example.com", "wrong") is None
    assert authenticate_user(db, "OWNER@example.com", "StrongPass!123").id == user.id

    user.is_active = False
    db.commit()
    assert authenticate_user(db, "owner@example.com", "StrongPass!123") is None
