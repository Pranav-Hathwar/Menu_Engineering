"""
app/services/analytics_service.py

Handles advanced querying and aggregation of sales data.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.models.sales import SalesData

def get_sales_summary(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Aggregates SalesData by item_name.
    Calculates the sum of quantity and sum of revenue per item.
    """
    # Create the base aggregation query
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label('total_quantity'),
        func.sum(SalesData.revenue).label('total_revenue')
    )
    
    # Apply optional date filters before grouping
    if start_date:
        query = query.filter(SalesData.date >= start_date)
    if end_date:
        query = query.filter(SalesData.date <= end_date)
        
    # Execute the aggregation
    results = query.group_by(SalesData.item_name).all()
    
    # Format the results into a list of dictionaries matching the Pydantic schema
    summary = []
    for row in results:
        summary.append({
            "item_name": row.item_name,
            # Handle potential None values if a group was fully empty (edge case)
            "total_quantity": row.total_quantity or 0,
            "total_revenue": row.total_revenue or 0.0
        })
        
    return summary

def get_menu_engineering_classification(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Classifies menu items into Stars, Plowhorses, Puzzles, and Dogs.
    Uses outer joins securely to grab popularity from SalesData and cost metrics from MenuItem.
    Returns classified dicts seamlessly matching the ItemClassification Pydantic schema.
    """
    from app.models.menu import MenuItem
    
    query = db.query(
        SalesData.item_name,
        func.sum(SalesData.quantity).label('total_quantity'),
        MenuItem.cost_price,
        MenuItem.selling_price
    ).outerjoin(
        MenuItem, SalesData.item_name == MenuItem.item_name
    )
    
    if start_date:
        query = query.filter(SalesData.date >= start_date)
    if end_date:
        query = query.filter(SalesData.date <= end_date)
        
    results = query.group_by(
        SalesData.item_name,
        MenuItem.cost_price,
        MenuItem.selling_price
    ).all()
    
    valid_items = []
    unlinked_items = []
    
    total_popularity = 0
    total_profitability = 0
    
    for row in results:
        item_name = row.item_name
        qty = row.total_quantity or 0
        
        # Edge case: Missing cost configuration (Unlinked Item)
        # We flag it and skip applying it to the global averages
        if row.cost_price is None or row.selling_price is None:
            unlinked_items.append({
                "item_name": item_name,
                "total_quantity": qty,
                "profit": 0.0,
                "category": "Unlinked Item"
            })
            continue
            
        profit_margin = row.selling_price - row.cost_price
        
        total_popularity += qty
        total_profitability += profit_margin
        
        valid_items.append({
            "item_name": item_name,
            "total_quantity": qty,
            "profit": profit_margin,
            "category": "" # To be scored
        })
        
    # Deterministic Global Metrics Mapping
    n_valid = len(valid_items)
    avg_pop = total_popularity / n_valid if n_valid > 0 else 0
    avg_prof = total_profitability / n_valid if n_valid > 0 else 0
    
    # Apply Standard Classification Rules
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
            
    # By returning left joined grouped items only, zero sales items are inherently excluded
    return valid_items + unlinked_items
