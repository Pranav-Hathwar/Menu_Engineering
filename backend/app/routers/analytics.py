"""
app/routers/analytics.py

Exposes the aggregated analytics endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.schemas.analytics import SalesSummary, ItemClassification, ItemRecommendation
from app.services.analytics_service import get_sales_summary, get_menu_engineering_classification
from app.services.recommendation_service import get_recommendations
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter()

@router.get("/summary", response_model=List[SalesSummary])
def get_analytics_summary(
    start_date: Optional[date] = Query(None, description="Starting date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Ending date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns an aggregated summary of total quantity and total revenue per item.
    """
    summary = get_sales_summary(db, start_date, end_date)
    return summary

@router.get("/classification", response_model=List[ItemClassification])
def get_classification(
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Classifies menu items into Stars, Plowhorses, Puzzles, and Dogs based on 
    average popularity and profitability.
    """
    return get_menu_engineering_classification(db, start_date, end_date)

@router.get("/recommendations", response_model=List[ItemRecommendation])
def get_actionable_recommendations(
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns rule-based business decisions tied to matrix classification.
    """
    return get_recommendations(db, start_date, end_date)
