"""
app/schemas/analytics.py

Pydantic schemas for formatting analytics engine outputs.
"""
from datetime import date

from pydantic import BaseModel

class SalesSummary(BaseModel):
    item_name: str
    total_quantity: int
    total_revenue: float

class DailySales(BaseModel):
    date: date
    total_revenue: float
    total_quantity: int
    total_profit: float
    line_items: int

class ItemClassification(BaseModel):
    item_name: str
    total_quantity: int
    total_revenue: float
    unit_cost: float
    profit: float
    category: str

class ItemRecommendation(BaseModel):
    item_name: str
    category: str
    recommendation: str
    reason: str
    priority: str
    confidence: float


class BusinessInsight(BaseModel):
    title: str
    value: str
    detail: str
    severity: str
