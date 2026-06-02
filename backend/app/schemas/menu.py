"""
app/schemas/menu.py

Pydantic schemas for the MenuItem model.
"""
from pydantic import BaseModel, ConfigDict

class MenuItemBase(BaseModel):
    item_name: str
    cost_price: float
    selling_price: float

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemResponse(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
