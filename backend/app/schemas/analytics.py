"""
app/schemas/analytics.py

Pydantic schemas for formatting analytics engine outputs.
"""
from datetime import date
from typing import List, Optional

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
    total_profit: float
    profit_margin: float
    # "recipe" when the cost comes from a defined bill-of-materials,
    # "upload" when it is the flat unit_cost from the ingested file.
    cost_source: str = "upload"
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


class TrendPoint(BaseModel):
    date: date
    total_revenue: float
    total_profit: float
    total_quantity: int
    ma_revenue: float


class WeekdayPerformance(BaseModel):
    weekday: str
    avg_revenue: float
    avg_quantity: float
    days_observed: int


class ParetoItem(BaseModel):
    item_name: str
    total_revenue: float
    revenue_share: float
    cumulative_share: float


class PeriodComparison(BaseModel):
    window_days: int
    current_start: date
    current_end: date
    previous_start: date
    previous_end: date
    current_revenue: float
    previous_revenue: float
    revenue_change_pct: Optional[float] = None
    current_profit: float
    previous_profit: float
    profit_change_pct: Optional[float] = None
    current_units: int
    previous_units: int
    units_change_pct: Optional[float] = None


class SalesTrends(BaseModel):
    daily: List[TrendPoint]
    weekday: List[WeekdayPerformance]
    pareto: List[ParetoItem]
    comparison: Optional[PeriodComparison] = None
