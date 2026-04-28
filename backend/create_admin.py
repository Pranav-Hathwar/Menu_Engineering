"""Create an initial owner account from environment variables.

Usage:
  $env:ADMIN_EMAIL="owner@example.com"
  $env:ADMIN_PASSWORD="StrongPass!123"
  python create_admin.py
"""

import os
import sys

from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import normalize_email
from app.utils.security import get_password_hash

admin_email = normalize_email(os.getenv("ADMIN_EMAIL", ""))
admin_password = os.getenv("ADMIN_PASSWORD", "")

if not admin_email or not admin_password:
    print("ERROR: Set ADMIN_EMAIL and ADMIN_PASSWORD before running this script.")
    sys.exit(1)

try:
    candidate = UserCreate(email=admin_email, password=admin_password)
except Exception as exc:
    print(f"ERROR: Invalid admin credentials: {exc}")
    sys.exit(1)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    if db.query(User).filter(User.email == candidate.email).first():
        print("SUCCESS: Admin user already exists")
    else:
        admin = User(email=candidate.email, hashed_password=get_password_hash(candidate.password), is_active=True)
        db.add(admin)
        db.commit()
        print("SUCCESS: Admin user created")
except Exception as exc:
    db.rollback()
    print(f"ERROR: {exc}")
    sys.exit(1)
finally:
    db.close()
