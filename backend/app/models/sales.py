"""
app/models/sales.py

Defines the SalesData model for SQLAlchemy.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SalesData(Base):
    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String, index=True, nullable=False, default="Default Restaurant")
    # Storing the item_name directly is useful for historical snapshots (denormalization)
    item_name = Column(String, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    revenue = Column(Float, nullable=False, default=0.0)
    unit_cost = Column(Float, nullable=False, default=0.0)
    date = Column(Date, index=True, nullable=False)

    # Linking to MenuItem creates a scalable relationship for deep analytics
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    
    menu_item = relationship("MenuItem", back_populates="sales")
