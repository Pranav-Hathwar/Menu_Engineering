"""
app/schemas/sales.py

Pydantic schemas for the SalesData model.
"""
from pydantic import BaseModel
from datetime import date
from typing import Optional

class SalesDataBase(BaseModel):
    item_name: str
    quantity: int
    revenue: float
    date: date
    menu_item_id: Optional[int] = None

class SalesDataCreate(SalesDataBase):
    pass

class SalesDataResponse(SalesDataBase):
    id: int

    class Config:
        from_attributes = True
