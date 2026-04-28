"""Rule-based business recommendations from menu classifications."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.services.analytics_service import get_menu_engineering_classification


def get_recommendations(
    db: Session,
    owner_id: int | None = None,
    restaurant_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    classifications = get_menu_engineering_classification(
        db, owner_id=owner_id, restaurant_name=restaurant_name, start_date=start_date, end_date=end_date
    )

    recommendations = []
    for item in classifications:
        category = item["category"]
        rec_data = {
            "item_name": item["item_name"],
            "category": category,
            "recommendation": "",
            "reason": "",
            "priority": "Medium",
            "confidence": 0.86,
        }

        if category == "Star":
            rec_data.update(
                recommendation="Protect quality and feature this item in high-visibility menu positions.",
                reason="High demand and high estimated per-unit profit.",
                priority="High",
                confidence=0.92,
            )
        elif category == "Plowhorse":
            rec_data.update(
                recommendation="Test a small price increase, reduce waste, or redesign portions without hurting demand.",
                reason="High demand but lower profit than the catalog average.",
                priority="High",
                confidence=0.88,
            )
        elif category == "Puzzle":
            rec_data.update(
                recommendation="Improve menu placement, naming, photography, and staff prompts before discounting.",
                reason="Healthy profit but demand is below the catalog average.",
                priority="Medium",
                confidence=0.84,
            )
        elif category == "Dog":
            rec_data.update(
                recommendation="Remove, rework, or bundle this item unless it has strategic value.",
                reason="Low demand and low estimated profit.",
                priority="Low",
                confidence=0.82,
            )

        recommendations.append(rec_data)

    return recommendations
