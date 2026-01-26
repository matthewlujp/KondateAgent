import pytest
from app.models.ingredient import Ingredient, IngredientSession


def test_ingredient_creation():
    ingredient = Ingredient(
        name="chicken breast",
        quantity="2",
        raw_input="2 chicken breasts",
        confidence=0.95,
    )
    assert ingredient.name == "chicken breast"
    assert ingredient.quantity == "2"
    assert ingredient.confidence == 0.95
    assert ingredient.id is not None


def test_ingredient_session_creation():
    session = IngredientSession(user_id="user_123")
    assert session.user_id == "user_123"
    assert session.ingredients == []
    assert session.status == "in_progress"
    assert session.id is not None


def test_session_add_ingredient():
    session = IngredientSession(user_id="user_123")
    ingredient = Ingredient(
        name="tomatoes",
        quantity="3",
        raw_input="3 tomatoes",
        confidence=0.9,
    )
    session.ingredients.append(ingredient)
    assert len(session.ingredients) == 1
    assert session.ingredients[0].name == "tomatoes"
