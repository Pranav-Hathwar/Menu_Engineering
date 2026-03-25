"""
app/services/analytics_service.py

Handles advanced querying and aggregation of sales data.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.models.sales import SalesData

def get_sales_summary(db: Session, restaurant_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None):
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label('total_quantity'),
        func.sum(SalesData.revenue).label('total_revenue')
    )
    
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)
    if start_date:
        query = query.filter(SalesData.date >= start_date)
    if end_date:
        query = query.filter(SalesData.date <= end_date)
        
    results = query.group_by(SalesData.item_name).all()
    
    summary = []
    for row in results:
        summary.append({
            "item_name": row.item_name,
            "total_quantity": row.total_quantity or 0,
            "total_revenue": row.total_revenue or 0.0
        })
        
    return summary

def get_menu_engineering_classification(db: Session, restaurant_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Classifies menu items into Stars, Plowhorses, Puzzles, and Dogs.
    Dynamically analyzes the uploaded raw Sales Data to calculate algorithmic Unit Revenue Proxies,
    completely bypassing the need for manual catalog pre-configuration!
    """
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label('total_quantity'),
        func.sum(SalesData.revenue).label('total_revenue'),
        func.sum(SalesData.unit_cost * SalesData.quantity).label('total_cost')
    )
    
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)
    if start_date:
        query = query.filter(SalesData.date >= start_date)
    if end_date:
        query = query.filter(SalesData.date <= end_date)
        
    results = query.group_by(SalesData.item_name).all()
    
    valid_items = []
    total_popularity = 0
    total_profitability = 0
    
    for row in results:
        item_name = row.item_name
        qty = row.total_quantity or 0
        rev = row.total_revenue or 0.0
        cogs = row.total_cost or 0.0
        
        # Calculate theoretical unit profit (Revenue - Cost per Unit)
        avg_unit_revenue = rev / qty if qty > 0 else 0
        avg_unit_cost = cogs / qty if qty > 0 else 0
        actual_profit_per_unit = avg_unit_revenue - avg_unit_cost
        
        total_popularity += qty
        total_profitability += actual_profit_per_unit
        
        valid_items.append({
            "item_name": item_name,
            "total_quantity": qty,
            "total_revenue": rev,
            "unit_cost": avg_unit_cost,
            "profit": actual_profit_per_unit,
            "category": "" # To be dynamically scored
        })
        
    # Deterministic Global Metrics Mapping
    n_valid = len(valid_items)
    avg_pop = total_popularity / n_valid if n_valid > 0 else 0
    avg_prof = total_profitability / n_valid if n_valid > 0 else 0
    
    # Apply Standard Classification Matrix Algorithms
    for item in valid_items:
        is_high_pop = item["total_quantity"] >= avg_pop
        is_high_prof = item["profit"] >= avg_prof
        
        if is_high_pop and is_high_prof:
            item["category"] = "Star"
        elif is_high_pop and not is_high_prof:
            item["category"] = "Plowhorse"
        elif not is_high_pop and is_high_prof:
            item["category"] = "Puzzle"
        else:
            item["category"] = "Dog"
            
    return valid_items
