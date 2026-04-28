"""
app/models/user.py

Defines the User model for SQLAlchemy.
This represents the users table in PostgreSQL.
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    sales_records = relationship("SalesData", back_populates="owner")
