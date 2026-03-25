"""
app/schemas/analytics.py

Pydantic schemas for formatting analytics engine outputs.
"""
from pydantic import BaseModel

class SalesSummary(BaseModel):
    item_name: str
    total_quantity: int
    total_revenue: float

class ItemClassification(BaseModel):
    item_name: str
    total_quantity: int
    profit: float
    category: str

class ItemRecommendation(BaseModel):
    item_name: str
    category: str
    recommendation: str
    reason: str
    priority: str
    confidence: float
