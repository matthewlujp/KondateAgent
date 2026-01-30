from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.recipe import Recipe
from app.models.meal_plan import MealSlot
from app.services.meal_plan_generator import (
    MealPlanGenerator,
    PlanAssignments,
    RecipeAssignment,
)
from datetime import datetime, UTC, timedelta


@pytest.fixture
def sample_recipes():
    """Create sample recipes for testing."""
    now = datetime.now(UTC)
    return [
        Recipe(
            id="recipe_1",
            source="youtube",
            source_id="vid1",
            url="https://youtube.com/watch?v=vid1",
            thumbnail_url="https://example.com/thumb1.jpg",
            title="Chicken Pasta",
            creator_name="Chef A",
            creator_id="chef_a",
            extracted_ingredients=["chicken", "pasta", "tomatoes"],
            raw_description="Delicious pasta",
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
            extracted_ingredients=["beef", "broccoli", "soy sauce"],
            raw_description="Quick stir fry",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        ),
        Recipe(
            id="recipe_3",
            source="youtube",
            source_id="vid3",
            url="https://youtube.com/watch?v=vid3",
            thumbnail_url="https://example.com/thumb3.jpg",
            title="Fish Tacos",
            creator_name="Chef C",
            creator_id="chef_c",
            extracted_ingredients=["fish", "tortillas", "cabbage"],
            raw_description="Fresh tacos",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        ),
    ]


@pytest.mark.asyncio
async def test_generate_normal_assignment(sample_recipes):
    """Test normal case: 3 recipes assigned to 3 enabled days."""
    generator = MealPlanGenerator()
    enabled_days = ["monday", "wednesday", "friday"]
    user_ingredients = ["chicken", "pasta", "beef", "fish"]

    # Mock OpenAI response
    mock_assignments = PlanAssignments(
        assignments=[
            RecipeAssignment(
                day="monday",
                recipe_id="recipe_1",
                reasoning="Uses chicken and pasta from user's ingredients",
            ),
            RecipeAssignment(
                day="wednesday",
                recipe_id="recipe_2",
                reasoning="Uses beef from user's ingredients",
            ),
            RecipeAssignment(
                day="friday",
                recipe_id="recipe_3",
                reasoning="Uses fish from user's ingredients",
            ),
        ]
    )

    mock_message = MagicMock()
    mock_message.parsed = mock_assignments
    mock_message.refusal = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    with patch(
        "app.services.meal_plan_generator.openai_client.beta.chat.completions.parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        slots = await generator.generate(sample_recipes, enabled_days, user_ingredients)

    assert len(slots) == 3
    assert slots[0].day == "monday"
    assert slots[0].recipe_id == "recipe_1"
    assert slots[0].enabled is True
    assert slots[1].day == "wednesday"
    assert slots[1].recipe_id == "recipe_2"
    assert slots[2].day == "friday"
    assert slots[2].recipe_id == "recipe_3"


@pytest.mark.asyncio
async def test_generate_fewer_recipes_than_days(sample_recipes):
    """Test when there are fewer recipes than enabled days."""
    generator = MealPlanGenerator()
    enabled_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    user_ingredients = ["chicken", "pasta"]

    # Mock OpenAI to return only 3 assignments for 5 days
    mock_assignments = PlanAssignments(
        assignments=[
            RecipeAssignment(
                day="monday",
                recipe_id="recipe_1",
                reasoning="Best match",
            ),
            RecipeAssignment(
                day="wednesday",
                recipe_id="recipe_2",
                reasoning="Good variety",
            ),
            RecipeAssignment(
                day="friday",
                recipe_id="recipe_3",
                reasoning="End of week",
            ),
        ]
    )

    mock_message = MagicMock()
    mock_message.parsed = mock_assignments
    mock_message.refusal = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    with patch(
        "app.services.meal_plan_generator.openai_client.beta.chat.completions.parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        slots = await generator.generate(sample_recipes, enabled_days, user_ingredients)

    # Should get 3 slots (only assigned days)
    assert len(slots) == 3
    assert all(slot.recipe_id is not None for slot in slots)


@pytest.mark.asyncio
async def test_generate_empty_recipes():
    """Test when no recipes are provided."""
    generator = MealPlanGenerator()
    enabled_days = ["monday", "wednesday"]
    user_ingredients = ["chicken"]

    slots = await generator.generate([], enabled_days, user_ingredients)

    assert len(slots) == 0


@pytest.mark.asyncio
async def test_generate_empty_days(sample_recipes):
    """Test when no days are enabled."""
    generator = MealPlanGenerator()
    enabled_days = []
    user_ingredients = ["chicken"]

    slots = await generator.generate(sample_recipes, enabled_days, user_ingredients)

    assert len(slots) == 0
