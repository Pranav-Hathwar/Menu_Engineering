"""
app/services/recommendation_service.py

Provides standard rule-based business logic recommendations based on derived classifications.
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.services.analytics_service import get_menu_engineering_classification

def get_recommendations(db: Session, restaurant_name: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None):
    # Retrieve the deterministically scored items
    classifications = get_menu_engineering_classification(db, restaurant_name, start_date, end_date)
    
    recommendations = []
    
    for item in classifications:
        category = item["category"]
        name = item["item_name"]
        
        # Base response template mapping to Pydantic schema
        rec_data = {
            "item_name": name,
            "category": category,
            "recommendation": "",
            "reason": "",
            "priority": "Medium",
            "confidence": 1.0  # As a strict rule-based algorithm, confidence is mathematically absolute (1.0).
        }
        
        if category == "Star":
            rec_data["recommendation"] = "Promote this item. Feature it prominently on the menu."
            rec_data["reason"] = "High demand and high profit margin."
            rec_data["priority"] = "High"
            
        elif category == "Plowhorse":
            rec_data["recommendation"] = "Increase price slightly OR reduce recipe cost."
            rec_data["reason"] = "High demand but under-performing profit margin."
            rec_data["priority"] = "High"
            
        elif category == "Puzzle":
            rec_data["recommendation"] = "Improve visibility on the menu. Rename or market better."
            rec_data["reason"] = "High profit margin but strictly low demand."
            rec_data["priority"] = "Medium"
            
        elif category == "Dog":
            rec_data["recommendation"] = "Consider removing item or completely reworking it."
            rec_data["reason"] = "Low demand and low profit margin."
            rec_data["priority"] = "Low"
            
        else:
            # Handle Edge cases ("Unlinked Item") produced by analytics_service
            rec_data["recommendation"] = "Define menu item cost and selling price in the items catalog."
            rec_data["reason"] = "Missing pricing configuration."
            rec_data["priority"] = "High"
            rec_data["confidence"] = 0.0 # We have 0.0 confidence in any business decision without prices.
            
        recommendations.append(rec_data)
        
    return recommendations
