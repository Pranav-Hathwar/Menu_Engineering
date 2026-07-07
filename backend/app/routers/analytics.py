"""Authenticated analytics endpoints."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sales import SalesData
from app.models.user import User
from app.schemas.analytics import (
    BusinessInsight,
    DailySales,
    ItemClassification,
    ItemRecommendation,
    MonthlyReport,
    SalesSummary,
    SalesTrends,
)
from app.services.analytics_service import (
    get_business_insights,
    get_daily_sales,
    get_menu_engineering_classification,
    get_sales_summary,
    get_sales_trends,
)
from app.services.report_service import get_monthly_report, list_available_months
from app.services.auth_service import get_current_user
from app.services.recommendation_service import get_recommendations

router = APIRouter()


@router.get("/summary", response_model=List[SalesSummary])
def get_analytics_summary(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sales_summary(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/daily", response_model=List[DailySales])
def get_daily_breakdown(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_daily_sales(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/classification", response_model=List[ItemClassification])
def get_classification(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_menu_engineering_classification(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/recommendations", response_model=List[ItemRecommendation])
def get_actionable_recommendations(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_recommendations(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/insights", response_model=List[BusinessInsight])
def get_insights(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_business_insights(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/trends", response_model=SalesTrends)
def get_trends(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    start_date: Optional[date] = Query(None, description="Starting date filter"),
    end_date: Optional[date] = Query(None, description="Ending date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sales_trends(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/monthly-report", response_model=MonthlyReport)
def get_month_report(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    month: Optional[str] = Query(None, description="Month as YYYY-MM; omit for the current month (1st → today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_monthly_report(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        month_key=month,
    )


@router.get("/months", response_model=List[str])
def get_available_months(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_available_months(db, owner_id=current_user.id, restaurant_name=restaurant_name)


@router.get("/restaurants", response_model=List[str])
def get_unique_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(SalesData.restaurant_name)
        .filter(SalesData.owner_id == current_user.id)
        .distinct()
        .order_by(SalesData.restaurant_name.asc())
        .all()
    )
    return [r[0] for r in results if r[0]]


@router.get("/raw")
def get_raw_uploaded_data(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(SalesData).filter(SalesData.owner_id == current_user.id)
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)

    results = query.order_by(SalesData.id.desc()).limit(limit).all()

    return [
        {
            "id": row.id,
            "date": row.date,
            "restaurant_name": row.restaurant_name,
            "item_name": row.item_name,
            "quantity": row.quantity,
            "revenue": row.revenue,
            "unit_cost": row.unit_cost,
        }
        for row in results
    ]
