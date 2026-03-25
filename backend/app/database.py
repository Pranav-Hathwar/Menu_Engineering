"""
app/database.py

Sets up the SQLAlchemy engine and session factory.
Every route that touches the DB gets a session via get_db() dependency injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# create_engine dynamically bridges SQLite and PostgreSQL.
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

# SessionLocal is the factory for database sessions.
# autocommit=False → we control commits manually (safer).
# autoflush=False  → we control when changes are sent to DB.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base is the parent class for all SQLAlchemy models.
# Every model (table) you create will inherit from this.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Automatically closes the session after the request completes,
    even if an error occurs (guaranteed by try/finally).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
