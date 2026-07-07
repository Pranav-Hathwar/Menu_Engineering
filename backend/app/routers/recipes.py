"""Ingredient + recipe (bill-of-materials) endpoints.

All routes are owner-scoped and take the restaurant explicitly, mirroring how
the analytics endpoints are filtered.
"""

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.recipes import IngredientCreate, IngredientResponse, RecipeResponse, RecipeUpdate
from app.services.auth_service import get_current_user
from app.services.recipe_service import (
    create_ingredient,
    delete_ingredient,
    delete_recipe,
    list_ingredients,
    list_recipes,
    set_recipe,
    update_ingredient,
)

router = APIRouter()


@router.get("/ingredients", response_model=List[IngredientResponse])
def get_ingredients(
    restaurant_name: str = Query(..., min_length=1, description="Restaurant the ingredients belong to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_ingredients(db, owner_id=current_user.id, restaurant_name=restaurant_name)


@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def add_ingredient(
    data: IngredientCreate,
    restaurant_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_ingredient(db, owner_id=current_user.id, restaurant_name=restaurant_name, data=data)


@router.put("/ingredients/{ingredient_id}", response_model=IngredientResponse)
def edit_ingredient(
    ingredient_id: int,
    data: IngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_ingredient(db, owner_id=current_user.id, ingredient_id=ingredient_id, data=data)


@router.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_ingredient(db, owner_id=current_user.id, ingredient_id=ingredient_id)
    return None


@router.get("", response_model=List[RecipeResponse])
@router.get("/", response_model=List[RecipeResponse], include_in_schema=False)
def get_recipes(
    restaurant_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_recipes(db, owner_id=current_user.id, restaurant_name=restaurant_name)


@router.put("/items/{item_name}", response_model=RecipeResponse)
def put_recipe(
    item_name: str,
    payload: RecipeUpdate,
    restaurant_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return set_recipe(
        db,
        owner_id=current_user.id,
        restaurant_name=restaurant_name,
        item_name=item_name,
        lines=payload.lines,
    )


@router.delete("/items/{item_name}")
def remove_recipe(
    item_name: str,
    restaurant_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_recipe(db, owner_id=current_user.id, restaurant_name=restaurant_name, item_name=item_name)
    return {"message": f"Removed recipe ({deleted} line(s))."}
