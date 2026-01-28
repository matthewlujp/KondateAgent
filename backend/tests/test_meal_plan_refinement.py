from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime, UTC, timedelta

from app.models.recipe import Recipe
from app.models.meal_plan import MealPlan, MealSlot, ChatMessage
from app.services.meal_plan_refinement import (
    MealPlanRefinementAgent,
    SwapDecision,
)


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
        Recipe(
            id="recipe_4",
            source="youtube",
            source_id="vid4",
            url="https://youtube.com/watch?v=vid4",
            thumbnail_url="https://example.com/thumb4.jpg",
            title="Vegetable Curry",
            creator_name="Chef D",
            creator_id="chef_d",
            extracted_ingredients=["chickpeas", "curry", "spinach"],
            raw_description="Healthy curry",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        ),
    ]


@pytest.fixture
def sample_plan():
    """Create a sample meal plan."""
    return MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        status="active",
        slots=[
            MealSlot(day="monday", recipe_id="recipe_1", enabled=True),
            MealSlot(day="wednesday", recipe_id="recipe_2", enabled=True),
            MealSlot(day="friday", recipe_id="recipe_3", enabled=True),
        ],
    )


def test_execute_swap_success(sample_plan, sample_recipes):
    """Test successful recipe swap."""
    agent = MealPlanRefinementAgent()

    result = agent.execute_swap(
        plan=sample_plan,
        day="monday",
        recipe_pool=sample_recipes,
        criteria="something lighter",
    )

    assert result.success is True
    assert result.day == "monday"
    assert result.old_recipe_id == "recipe_1"
    # Should swap to recipe_4 (the only unassigned recipe)
    assert result.new_recipe_id == "recipe_4"
    assert "swapped" in result.message.lower()


def test_execute_swap_invalid_day(sample_plan, sample_recipes):
    """Test swap with invalid day."""
    agent = MealPlanRefinementAgent()

    result = agent.execute_swap(
        plan=sample_plan,
        day="tuesday",  # No slot for Tuesday
        recipe_pool=sample_recipes,
        criteria="anything",
    )

    assert result.success is False
    assert "no meal planned" in result.message.lower()


def test_execute_swap_avoids_assigned_recipes(sample_plan, sample_recipes):
    """Test that swap avoids recipes already assigned to other days."""
    agent = MealPlanRefinementAgent()

    # All recipes except recipe_4 are already assigned
    result = agent.execute_swap(
        plan=sample_plan,
        day="monday",
        recipe_pool=sample_recipes,
        criteria="different protein",
    )

    assert result.success is True
    # Should get recipe_4 (the only unassigned one)
    assert result.new_recipe_id == "recipe_4"
    # Should not get recipe_2 or recipe_3 (assigned to other days)
    assert result.new_recipe_id not in ["recipe_2", "recipe_3"]


def test_execute_swap_no_alternatives(sample_plan, sample_recipes):
    """Test swap when no alternative recipes available."""
    agent = MealPlanRefinementAgent()

    # Only provide recipes that are already assigned
    limited_pool = [r for r in sample_recipes if r.id in ["recipe_1", "recipe_2", "recipe_3"]]

    result = agent.execute_swap(
        plan=sample_plan,
        day="monday",
        recipe_pool=limited_pool,
        criteria="something else",
    )

    assert result.success is False
    assert "no alternative" in result.message.lower()


@pytest.mark.asyncio
async def test_process_message_with_swap(sample_plan, sample_recipes):
    """Test processing a message that triggers a swap."""
    agent = MealPlanRefinementAgent()

    # Mock LLM to decide to swap
    mock_decision = SwapDecision(
        should_swap=True,
        day="monday",
        criteria="lighter meal",
        response_text="I'll swap Monday's meal for something lighter.",
    )

    mock_message = MagicMock()
    mock_message.parsed = mock_decision
    mock_message.refusal = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    with patch(
        "app.services.meal_plan_refinement.openai_client.beta.chat.completions.parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response_text, tool_calls = await agent.process_message(
            message="Can you swap Monday for something lighter?",
            plan=sample_plan,
            recipe_pool=sample_recipes,
            chat_history=[],
        )

    assert "swap" in response_text.lower()
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "swap_meal"


@pytest.mark.asyncio
async def test_process_message_no_swap(sample_plan, sample_recipes):
    """Test processing a message that doesn't trigger a swap."""
    agent = MealPlanRefinementAgent()

    # Mock LLM to decide NOT to swap
    mock_decision = SwapDecision(
        should_swap=False,
        day=None,
        criteria=None,
        response_text="Your current plan looks great! All the meals use your available ingredients efficiently.",
    )

    mock_message = MagicMock()
    mock_message.parsed = mock_decision
    mock_message.refusal = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    with patch(
        "app.services.meal_plan_refinement.openai_client.beta.chat.completions.parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response_text, tool_calls = await agent.process_message(
            message="This plan looks good!",
            plan=sample_plan,
            recipe_pool=sample_recipes,
            chat_history=[],
        )

    assert "looks great" in response_text.lower()
    assert len(tool_calls) == 0
