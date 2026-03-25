"""
app/models/menu.py

Defines the MenuItem model for SQLAlchemy.
"""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True, index=True, nullable=False)
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)

    # 1-to-Many relationship: A single menu item can have many sales records.
    sales = relationship("SalesData", back_populates="menu_item")
