from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, UTC, timedelta

from app.main import app
from app.auth import create_access_token
from app.models.ingredient import IngredientSession, Ingredient
from app.models.recipe import Recipe
from app.models.meal_plan import MealPlan, MealSlot
from app.services.session_store import session_store
from app.services.recipe_cache import recipe_cache
from app.services.meal_plan_store import meal_plan_store


# Test user credentials
TEST_USER = "test_user_123"


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    token = create_access_token(TEST_USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all stores before each test."""
    session_store._sessions.clear()
    session_store._user_sessions.clear()
    recipe_cache._recipes.clear()
    meal_plan_store._plans.clear()
    meal_plan_store._user_plans.clear()
    meal_plan_store._sessions.clear()
    meal_plan_store._plan_sessions.clear()
    yield


@pytest.fixture
def sample_session():
    """Create a sample ingredient session."""
    session = IngredientSession(
        user_id=TEST_USER,
        ingredients=[
            Ingredient(
                name="chicken",
                quantity="1",
                unit="lb",
                raw_input="chicken breast",
                confidence=0.9,
            )
        ],
    )
    session_store._sessions[session.id] = session
    session_store._user_sessions[TEST_USER] = [session.id]
    return session


@pytest.fixture
def sample_recipes():
    """Create and cache sample recipes."""
    now = datetime.now(UTC)
    recipes = [
        Recipe(
            id="recipe_1",
            source="youtube",
            source_id="vid1",
            url="https://youtube.com/watch?v=vid1",
            thumbnail_url="https://example.com/thumb1.jpg",
            title="Chicken Pasta",
            creator_name="Chef A",
            creator_id="chef_a",
            extracted_ingredients=["chicken", "pasta"],
            raw_description="Pasta",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        ),
        Recipe(
            id="recipe_2",
            source="youtube",
            source_id="vid2",
            url="https://youtube.com/watch?v=vid2",
            thumbnail_url="https://example.com/thumb2.jpg",
            title="Beef Stir Fry",
            creator_name="Chef B",
            creator_id="chef_b",
            extracted_ingredients=["beef", "broccoli"],
            raw_description="Stir fry",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        ),
    ]

    for recipe in recipes:
        recipe_cache._recipes[recipe.id] = recipe

    return recipes


@pytest.mark.asyncio
async def test_generate_plan_success(sample_session, sample_recipes, auth_headers):
    """Test successful plan generation."""
    with patch(
        "app.routers.meal_plans.generator.generate",
        new_callable=AsyncMock,
        return_value=[
            MealSlot(day="monday", recipe_id="recipe_1", enabled=True),
            MealSlot(day="wednesday", recipe_id="recipe_2", enabled=True),
        ],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/meal-plans",
                json={
                    "ingredient_session_id": sample_session.id,
                    "enabled_days": ["monday", "wednesday"],
                    "recipe_ids": ["recipe_1", "recipe_2"],
                },
                headers=auth_headers,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == TEST_USER
    assert data["ingredient_session_id"] == sample_session.id
    assert data["status"] == "active"
    assert len(data["slots"]) >= 2


@pytest.mark.asyncio
async def test_generate_plan_unauthorized():
    """Test plan generation without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/meal-plans",
            json={
                "ingredient_session_id": "session_123",
                "enabled_days": ["monday"],
                "recipe_ids": ["recipe_1"],
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_plan_session_not_found(sample_recipes, auth_headers):
    """Test plan generation with nonexistent session."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/meal-plans",
            json={
                "ingredient_session_id": "nonexistent_session",
                "enabled_days": ["monday"],
                "recipe_ids": ["recipe_1"],
            },
            headers=auth_headers,
        )

    assert response.status_code == 404
    assert "session not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_plan_wrong_user(sample_recipes, auth_headers):
    """Test plan generation with another user's session."""
    # Create session for different user
    other_session = IngredientSession(user_id="other_user")
    session_store._sessions[other_session.id] = other_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/meal-plans",
            json={
                "ingredient_session_id": other_session.id,
                "enabled_days": ["monday"],
                "recipe_ids": ["recipe_1"],
            },
            headers=auth_headers,
        )

    assert response.status_code == 403
    assert "another user" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_plan_success(auth_headers):
    """Test getting an existing plan."""
    plan = MealPlan(
        user_id=TEST_USER,
        ingredient_session_id="session_123",
        slots=[MealSlot(day="monday", recipe_id="recipe_1")],
    )
    meal_plan_store.save_plan(plan)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/meal-plans/{plan.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == plan.id
    assert data["user_id"] == TEST_USER
    assert len(data["slots"]) == 1


@pytest.mark.asyncio
async def test_get_plan_not_found(auth_headers):
    """Test getting a nonexistent plan."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/meal-plans/nonexistent_plan", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_plan_wrong_user(auth_headers):
    """Test getting another user's plan."""
    plan = MealPlan(
        user_id="other_user",
        ingredient_session_id="session_123",
    )
    meal_plan_store.save_plan(plan)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/meal-plans/{plan.id}", headers=auth_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_success(sample_recipes, auth_headers):
    """Test sending a chat message."""
    plan = MealPlan(
        user_id=TEST_USER,
        ingredient_session_id="session_123",
        status="active",
        slots=[
            MealSlot(day="monday", recipe_id="recipe_1", enabled=True),
            MealSlot(day="wednesday", recipe_id="recipe_2", enabled=True),
        ],
    )
    meal_plan_store.save_plan(plan)

    # Cache recipes
    for recipe in sample_recipes:
        recipe_cache._recipes[recipe.id] = recipe

    with patch(
        "app.routers.meal_plans.refinement_agent.process_message",
        new_callable=AsyncMock,
        return_value=("I'll swap Monday's meal for you.", []),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/meal-plans/{plan.id}/chat",
                json={"message": "Can you swap Monday?"},
                headers=auth_headers,
            )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "plan" in data
    assert "tool_calls" in data


@pytest.mark.asyncio
async def test_chat_plan_not_found(auth_headers):
    """Test chat with nonexistent plan."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/meal-plans/nonexistent_plan/chat",
            json={"message": "Hello"},
            headers=auth_headers,
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_empty_message(auth_headers):
    """Test chat with empty message."""
    plan = MealPlan(user_id=TEST_USER, ingredient_session_id="session_123")
    meal_plan_store.save_plan(plan)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/meal-plans/{plan.id}/chat",
            json={"message": ""},
            headers=auth_headers,
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_response_includes_recipe_data(sample_session, sample_recipes, auth_headers):
    """Test that chat response includes full recipe data for swapped meals.

    This ensures the frontend can display swapped recipes even if they
    weren't in the original sessionStorage recipe list.
    """
    # Add a third recipe that will be swapped in
    now = datetime.now(UTC)
    new_recipe = Recipe(
        id="recipe_3",
        source="youtube",
        source_id="vid3",
        url="https://youtube.com/watch?v=vid3",
        thumbnail_url="https://example.com/thumb3.jpg",
        title="Japanese Ramen",
        creator_name="Chef C",
        creator_id="chef_c",
        extracted_ingredients=["ramen", "pork", "egg"],
        raw_description="Authentic ramen",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )
    recipe_cache._recipes[new_recipe.id] = new_recipe

    plan = MealPlan(
        user_id=TEST_USER,
        ingredient_session_id=sample_session.id,
        status="active",
        slots=[
            MealSlot(day="monday", recipe_id="recipe_1", enabled=True),
            MealSlot(day="wednesday", recipe_id="recipe_2", enabled=True),
        ],
    )
    meal_plan_store.save_plan(plan)

    # Mock refinement agent to simulate a swap to recipe_3
    async def mock_process_message(message, plan, recipe_pool, chat_history):
        # Simulate swapping Monday to recipe_3
        for slot in plan.slots:
            if slot.day == "monday":
                slot.recipe_id = "recipe_3"
                slot.swap_count += 1
                break
        tool_call = {
            "id": "call_swap_monday",
            "type": "function",
            "function": {
                "name": "swap_meal",
                "arguments": '{"day": "monday", "old_recipe": "recipe_1", "new_recipe": "recipe_3"}',
            },
        }
        return "I've swapped Monday to Japanese Ramen.", [tool_call]

    with patch(
        "app.routers.meal_plans.refinement_agent.process_message",
        new_callable=AsyncMock,
        side_effect=mock_process_message,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/meal-plans/{plan.id}/chat",
                json={"message": "Swap Monday to something Japanese"},
                headers=auth_headers,
            )

    assert response.status_code == 200
    data = response.json()

    # The response should include recipe data
    assert "recipes" in data, "Response should include 'recipes' field with full recipe data"

    # Should have recipe data for all assigned slots
    recipes_by_id = {r["id"]: r for r in data["recipes"]}
    assert "recipe_3" in recipes_by_id, "Swapped recipe (recipe_3) should be in recipes"
    assert recipes_by_id["recipe_3"]["title"] == "Japanese Ramen"
