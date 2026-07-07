"""
app/models/ingredient.py

Ingredient catalog + recipe lines (bill-of-materials).

A menu item's true cost is the sum of its recipe lines:
    cost(item) = Σ line.quantity × ingredient.cost_per_unit
When a recipe exists for an item, analytics uses this computed cost instead of
the flat per-row ``unit_cost`` captured at upload time — so updating one
ingredient price immediately corrects the margins of every dish using it.
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        UniqueConstraint("owner_id", "restaurant_name", "name", name="uq_ingredient_owner_restaurant_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    restaurant_name = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    # Free-form unit label the cost is quoted in: "kg", "litre", "piece", ...
    unit = Column(String, nullable=False, default="unit")
    cost_per_unit = Column(Float, nullable=False, default=0.0)

    recipe_lines = relationship("RecipeLine", back_populates="ingredient", cascade="all, delete-orphan")


class RecipeLine(Base):
    __tablename__ = "recipe_lines"
    __table_args__ = (
        UniqueConstraint("owner_id", "restaurant_name", "item_name", "ingredient_id", name="uq_recipe_line"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    restaurant_name = Column(String, index=True, nullable=False)
    # Matches SalesData.item_name (title-cased by the ingestion pipeline).
    item_name = Column(String, index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    # Amount of the ingredient (in its unit) used per one unit sold.
    quantity = Column(Float, nullable=False, default=0.0)

    ingredient = relationship("Ingredient", back_populates="recipe_lines")
