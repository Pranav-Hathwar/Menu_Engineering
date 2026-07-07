"""Pydantic schemas for ingredients and recipes (bill-of-materials)."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    unit: str = Field(default="unit", min_length=1, max_length=40)
    cost_per_unit: float = Field(ge=0)


class IngredientResponse(IngredientCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_name: str


class RecipeLineInput(BaseModel):
    ingredient_id: int
    # Amount of the ingredient used per one unit sold, in the ingredient's unit.
    quantity: float = Field(gt=0)


class RecipeUpdate(BaseModel):
    lines: List[RecipeLineInput]


class RecipeLineResponse(BaseModel):
    ingredient_id: int
    ingredient_name: str
    unit: str
    cost_per_unit: float
    quantity: float
    line_cost: float


class RecipeResponse(BaseModel):
    item_name: str
    lines: List[RecipeLineResponse]
    unit_cost: float
