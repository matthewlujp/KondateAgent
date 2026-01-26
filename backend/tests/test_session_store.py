import pytest
from app.services.session_store import SessionStore
from app.models import Ingredient, IngredientSession


@pytest.fixture
def store():
    return SessionStore()


@pytest.fixture
def sample_ingredient():
    return Ingredient(
        name="chicken",
        quantity="2",
        raw_input="2 chicken breasts",
        confidence=0.9,
    )


def test_create_session(store):
    session = store.create_session("user_123")
    assert session.user_id == "user_123"
    assert session.status == "in_progress"
    assert len(session.ingredients) == 0


def test_get_session(store):
    created = store.create_session("user_123")
    retrieved = store.get_session(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_nonexistent_session(store):
    result = store.get_session("nonexistent")
    assert result is None


def test_get_latest_session(store):
    store.create_session("user_123")
    latest = store.create_session("user_123")

    result = store.get_latest_session("user_123")
    assert result is not None
    assert result.id == latest.id


def test_add_ingredients(store, sample_ingredient):
    session = store.create_session("user_123")
    updated = store.add_ingredients(session.id, [sample_ingredient])

    assert updated is not None
    assert len(updated.ingredients) == 1
    assert updated.ingredients[0].name == "chicken"


def test_remove_ingredient(store, sample_ingredient):
    session = store.create_session("user_123")
    store.add_ingredients(session.id, [sample_ingredient])

    updated = store.remove_ingredient(session.id, sample_ingredient.id)
    assert updated is not None
    assert len(updated.ingredients) == 0


def test_update_session_status(store):
    session = store.create_session("user_123")
    updated = store.update_status(session.id, "confirmed")

    assert updated is not None
    assert updated.status == "confirmed"
