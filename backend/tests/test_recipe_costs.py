"""Tests for ingredient/recipe management and recipe-cost analytics overrides."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")

import datetime as dt

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.ingredient import Ingredient
from app.models.sales import SalesData
from app.models.user import User
from app.schemas.recipes import RecipeLineInput
from app.services.analytics_service import get_daily_sales, get_menu_engineering_classification
from app.services.recipe_service import (
    delete_ingredient,
    delete_recipe,
    get_recipe_costs,
    set_recipe,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    user = User(email="owner@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user


def add_ingredient(db, owner_id, name, unit, cost):
    ingredient = Ingredient(
        owner_id=owner_id, restaurant_name="Recipe Cafe", name=name, unit=unit, cost_per_unit=cost
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


def seed_sales(db, owner_id):
    # 5 Dosas at Rs 100 each with a flat (wrong) unit_cost of 10.
    db.add(
        SalesData(
            restaurant_name="Recipe Cafe", item_name="Masala Dosa", quantity=5,
            revenue=500.0, unit_cost=10.0, date=dt.date(2026, 6, 1), owner_id=owner_id,
        )
    )
    db.commit()


def test_recipe_cost_is_sum_of_lines():
    db, user = make_session()
    rice = add_ingredient(db, user.id, "Rice batter", "kg", 60.0)
    potato = add_ingredient(db, user.id, "Potato filling", "kg", 40.0)

    set_recipe(
        db, user.id, "Recipe Cafe", "Masala Dosa",
        [RecipeLineInput(ingredient_id=rice.id, quantity=0.2),
         RecipeLineInput(ingredient_id=potato.id, quantity=0.25)],
    )

    costs = get_recipe_costs(db, user.id, "Recipe Cafe")
    # 0.2*60 + 0.25*40 = 12 + 10 = 22
    assert costs == {"Masala Dosa": pytest.approx(22.0)}


def test_recipe_cost_overrides_flat_unit_cost_in_analytics():
    db, user = make_session()
    seed_sales(db, user.id)
    rice = add_ingredient(db, user.id, "Rice batter", "kg", 60.0)

    # Without a recipe: flat unit_cost 10 -> profit/unit 90.
    items = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Recipe Cafe")
    assert items[0]["unit_cost"] == pytest.approx(10.0)
    assert items[0]["cost_source"] == "upload"

    set_recipe(db, user.id, "Recipe Cafe", "Masala Dosa",
               [RecipeLineInput(ingredient_id=rice.id, quantity=0.5)])  # 0.5*60 = 30

    items = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Recipe Cafe")
    assert items[0]["unit_cost"] == pytest.approx(30.0)
    assert items[0]["profit"] == pytest.approx(70.0)
    assert items[0]["total_profit"] == pytest.approx(350.0)
    assert items[0]["cost_source"] == "recipe"

    daily = get_daily_sales(db, owner_id=user.id, restaurant_name="Recipe Cafe")
    # 500 revenue - 5 * 30 recipe cost
    assert daily[0]["total_profit"] == pytest.approx(350.0)


def test_updating_ingredient_price_moves_margins():
    db, user = make_session()
    seed_sales(db, user.id)
    rice = add_ingredient(db, user.id, "Rice batter", "kg", 60.0)
    set_recipe(db, user.id, "Recipe Cafe", "Masala Dosa",
               [RecipeLineInput(ingredient_id=rice.id, quantity=0.5)])

    rice.cost_per_unit = 100.0  # price shock: 0.5*100 = 50/unit
    db.commit()

    items = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Recipe Cafe")
    assert items[0]["unit_cost"] == pytest.approx(50.0)
    assert items[0]["profit"] == pytest.approx(50.0)


def test_delete_recipe_restores_upload_cost_and_ingredient_guard():
    db, user = make_session()
    seed_sales(db, user.id)
    rice = add_ingredient(db, user.id, "Rice batter", "kg", 60.0)
    set_recipe(db, user.id, "Recipe Cafe", "Masala Dosa",
               [RecipeLineInput(ingredient_id=rice.id, quantity=0.5)])

    # An ingredient used by a recipe cannot be deleted.
    with pytest.raises(HTTPException) as exc:
        delete_ingredient(db, user.id, rice.id)
    assert exc.value.status_code == 409

    delete_recipe(db, user.id, "Recipe Cafe", "Masala Dosa")
    items = get_menu_engineering_classification(db, owner_id=user.id, restaurant_name="Recipe Cafe")
    assert items[0]["unit_cost"] == pytest.approx(10.0)
    assert items[0]["cost_source"] == "upload"

    # Now unused, the ingredient can be removed.
    delete_ingredient(db, user.id, rice.id)
    assert db.query(Ingredient).count() == 0


def test_set_recipe_rejects_unknown_and_duplicate_ingredients():
    db, user = make_session()
    rice = add_ingredient(db, user.id, "Rice batter", "kg", 60.0)

    with pytest.raises(HTTPException) as exc:
        set_recipe(db, user.id, "Recipe Cafe", "Masala Dosa",
                   [RecipeLineInput(ingredient_id=999, quantity=1.0)])
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        set_recipe(db, user.id, "Recipe Cafe", "Masala Dosa",
                   [RecipeLineInput(ingredient_id=rice.id, quantity=1.0),
                    RecipeLineInput(ingredient_id=rice.id, quantity=2.0)])
    assert exc.value.status_code == 400
