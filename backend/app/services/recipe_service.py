"""Ingredient catalog and recipe (bill-of-materials) business logic.

The headline export is :func:`get_recipe_costs`: a map of item_name to its
current recipe cost, which analytics uses to override the flat per-row
``unit_cost`` wherever a recipe is defined.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.ingredient import Ingredient, RecipeLine


# --------------------------------------------------------------------------
# Ingredients
# --------------------------------------------------------------------------

def list_ingredients(db: Session, owner_id: int, restaurant_name: str):
    return (
        db.query(Ingredient)
        .filter(Ingredient.owner_id == owner_id, Ingredient.restaurant_name == restaurant_name)
        .order_by(Ingredient.name.asc())
        .all()
    )


def create_ingredient(db: Session, owner_id: int, restaurant_name: str, data):
    ingredient = Ingredient(
        owner_id=owner_id,
        restaurant_name=restaurant_name,
        name=data.name.strip(),
        unit=data.unit.strip(),
        cost_per_unit=data.cost_per_unit,
    )
    db.add(ingredient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An ingredient named '{data.name.strip()}' already exists for this restaurant.",
        ) from exc
    db.refresh(ingredient)
    return ingredient


def update_ingredient(db: Session, owner_id: int, ingredient_id: int, data):
    ingredient = _owned_ingredient(db, owner_id, ingredient_id)
    ingredient.name = data.name.strip()
    ingredient.unit = data.unit.strip()
    ingredient.cost_per_unit = data.cost_per_unit
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An ingredient named '{data.name.strip()}' already exists for this restaurant.",
        ) from exc
    db.refresh(ingredient)
    return ingredient


def delete_ingredient(db: Session, owner_id: int, ingredient_id: int):
    ingredient = _owned_ingredient(db, owner_id, ingredient_id)
    used_by = (
        db.query(RecipeLine.item_name)
        .filter(RecipeLine.ingredient_id == ingredient.id)
        .distinct()
        .all()
    )
    if used_by:
        names = ", ".join(sorted(row[0] for row in used_by)[:5])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ingredient is used by recipe(s): {names}. Remove it from those recipes first.",
        )
    db.delete(ingredient)
    db.commit()


def _owned_ingredient(db: Session, owner_id: int, ingredient_id: int) -> Ingredient:
    ingredient = (
        db.query(Ingredient)
        .filter(Ingredient.owner_id == owner_id, Ingredient.id == ingredient_id)
        .first()
    )
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found.")
    return ingredient


# --------------------------------------------------------------------------
# Recipes
# --------------------------------------------------------------------------

def list_recipes(db: Session, owner_id: int, restaurant_name: str):
    lines = (
        db.query(RecipeLine)
        .options(joinedload(RecipeLine.ingredient))
        .filter(RecipeLine.owner_id == owner_id, RecipeLine.restaurant_name == restaurant_name)
        .order_by(RecipeLine.item_name.asc(), RecipeLine.id.asc())
        .all()
    )
    recipes: dict[str, list[RecipeLine]] = {}
    for line in lines:
        recipes.setdefault(line.item_name, []).append(line)
    return [_serialize_recipe(item_name, item_lines) for item_name, item_lines in recipes.items()]


def set_recipe(db: Session, owner_id: int, restaurant_name: str, item_name: str, lines):
    """Replace an item's whole recipe atomically (idempotent PUT semantics)."""
    item_name = item_name.strip()
    if not item_name:
        raise HTTPException(status_code=400, detail="Item name is required.")

    ingredient_ids = [line.ingredient_id for line in lines]
    if len(set(ingredient_ids)) != len(ingredient_ids):
        raise HTTPException(status_code=400, detail="A recipe cannot list the same ingredient twice.")

    owned = {
        ingredient.id: ingredient
        for ingredient in db.query(Ingredient).filter(
            Ingredient.owner_id == owner_id,
            Ingredient.restaurant_name == restaurant_name,
            Ingredient.id.in_(ingredient_ids),
        )
    }
    missing = [str(iid) for iid in ingredient_ids if iid not in owned]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown ingredient id(s): {', '.join(missing)}.")

    db.query(RecipeLine).filter(
        RecipeLine.owner_id == owner_id,
        RecipeLine.restaurant_name == restaurant_name,
        RecipeLine.item_name == item_name,
    ).delete(synchronize_session=False)

    new_lines = [
        RecipeLine(
            owner_id=owner_id,
            restaurant_name=restaurant_name,
            item_name=item_name,
            ingredient_id=line.ingredient_id,
            quantity=line.quantity,
        )
        for line in lines
    ]
    db.add_all(new_lines)
    db.commit()

    for line in new_lines:
        line.ingredient = owned[line.ingredient_id]
    return _serialize_recipe(item_name, new_lines)


def delete_recipe(db: Session, owner_id: int, restaurant_name: str, item_name: str) -> int:
    deleted = (
        db.query(RecipeLine)
        .filter(
            RecipeLine.owner_id == owner_id,
            RecipeLine.restaurant_name == restaurant_name,
            RecipeLine.item_name == item_name.strip(),
        )
        .delete(synchronize_session=False)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="No recipe found for this item.")
    db.commit()
    return deleted


def get_recipe_costs(db: Session, owner_id: int | None, restaurant_name: str | None) -> dict[str, float]:
    """item_name -> current recipe cost per unit sold, for analytics overrides.

    Returns an empty dict when the filters are absent (recipes are scoped to a
    single restaurant, so cross-restaurant analytics keep the flat unit_cost).
    """
    if owner_id is None or not restaurant_name:
        return {}

    lines = (
        db.query(RecipeLine)
        .options(joinedload(RecipeLine.ingredient))
        .filter(RecipeLine.owner_id == owner_id, RecipeLine.restaurant_name == restaurant_name)
        .all()
    )
    costs: dict[str, float] = {}
    for line in lines:
        costs[line.item_name] = costs.get(line.item_name, 0.0) + _line_cost(line)
    return costs


def _line_cost(line: RecipeLine) -> float:
    return (line.quantity or 0.0) * (line.ingredient.cost_per_unit or 0.0)


def _serialize_recipe(item_name: str, lines: list[RecipeLine]) -> dict:
    serialized = [
        {
            "ingredient_id": line.ingredient_id,
            "ingredient_name": line.ingredient.name,
            "unit": line.ingredient.unit,
            "cost_per_unit": line.ingredient.cost_per_unit,
            "quantity": line.quantity,
            "line_cost": round(_line_cost(line), 4),
        }
        for line in lines
    ]
    return {
        "item_name": item_name,
        "lines": serialized,
        "unit_cost": round(sum(entry["line_cost"] for entry in serialized), 4),
    }
