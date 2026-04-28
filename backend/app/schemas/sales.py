"""Pydantic schemas for sales records."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SalesDataBase(BaseModel):
    restaurant_name: str = Field(default="Default Restaurant", min_length=1, max_length=160)
    item_name: str = Field(min_length=1, max_length=240)
    quantity: int = Field(ge=0)
    revenue: float = Field(ge=0)
    unit_cost: float = Field(default=0.0, ge=0)
    date: date
    menu_item_id: Optional[int] = None


class SalesDataCreate(SalesDataBase):
    pass


class SalesDataResponse(SalesDataBase):
    id: int
    owner_id: Optional[int] = None
    upload_batch_id: Optional[str] = None

    class Config:
        from_attributes = True
