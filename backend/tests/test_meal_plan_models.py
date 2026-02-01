from datetime import datetime, UTC
import pytest

from app.models.meal_plan import (
    DayOfWeek,
    ALL_DAYS,
    MealSlot,
    MealPlan,
    ChatMessage,
    RefinementSession,
)


def test_meal_slot_defaults():
    """Test MealSlot with default values."""
    slot = MealSlot(day="monday")

    assert slot.id  # UUID generated
    assert slot.day == "monday"
    assert slot.enabled is True
    assert slot.recipe_id is None
    assert slot.assigned_at is None
    assert slot.swap_count == 0


def test_meal_slot_disabled():
    """Test creating a disabled MealSlot."""
    slot = MealSlot(day="sunday", enabled=False)

    assert slot.day == "sunday"
    assert slot.enabled is False


def test_meal_slot_with_recipe():
    """Test MealSlot with assigned recipe."""
    now = datetime.now(UTC)
    slot = MealSlot(
        day="tuesday",
        enabled=True,
        recipe_id="recipe_123",
        assigned_at=now,
        swap_count=2,
    )

    assert slot.day == "tuesday"
    assert slot.enabled is True
    assert slot.recipe_id == "recipe_123"
    assert slot.assigned_at == now
    assert slot.swap_count == 2


def test_all_days_constant():
    """Test ALL_DAYS constant includes all 7 days."""
    assert len(ALL_DAYS) == 7
    assert "monday" in ALL_DAYS
    assert "tuesday" in ALL_DAYS
    assert "wednesday" in ALL_DAYS
    assert "thursday" in ALL_DAYS
    assert "friday" in ALL_DAYS
    assert "saturday" in ALL_DAYS
    assert "sunday" in ALL_DAYS


def test_day_of_week_validation():
    """Test that DayOfWeek validates to correct days."""
    # Valid days should work
    for day in ALL_DAYS:
        slot = MealSlot(day=day)
        assert slot.day == day

    # Invalid day should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        MealSlot(day="funday")


def test_meal_plan_defaults():
    """Test MealPlan with default values."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )

    assert plan.id  # UUID generated
    assert plan.user_id == "user_123"
    assert plan.ingredient_session_id == "session_456"
    assert plan.status == "draft"
    assert plan.created_at <= datetime.now(UTC)
    assert len(plan.slots) == 0


def test_meal_plan_with_slots():
    """Test MealPlan with slots."""
    slots = [
        MealSlot(day="monday", recipe_id="recipe_1"),
        MealSlot(day="tuesday", recipe_id="recipe_2"),
        MealSlot(day="wednesday", enabled=False),
    ]

    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        slots=slots,
        status="active",
    )

    assert plan.status == "active"
    assert len(plan.slots) == 3
    assert plan.slots[0].day == "monday"
    assert plan.slots[1].day == "tuesday"
    assert plan.slots[2].enabled is False


def test_meal_plan_status_validation():
    """Test that MealPlan status is validated."""
    # Valid statuses
    plan_draft = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        status="draft",
    )
    assert plan_draft.status == "draft"

    plan_active = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        status="active",
    )
    assert plan_active.status == "active"

    # Invalid status should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        MealPlan(
            user_id="user_123",
            ingredient_session_id="session_456",
            status="completed",  # Invalid
        )


def test_chat_message_user():
    """Test creating a user ChatMessage."""
    message = ChatMessage(
        role="user",
        content="Can you swap Tuesday's meal?",
    )

    assert message.role == "user"
    assert message.content == "Can you swap Tuesday's meal?"
    assert message.tool_calls is None
    assert message.timestamp <= datetime.now(UTC)


def test_chat_message_assistant():
    """Test creating an assistant ChatMessage."""
    tool_calls = [
        {
            "id": "call_123",
            "type": "function",
            "function": {"name": "swap_meal", "arguments": '{"day": "tuesday"}'},
        }
    ]

    message = ChatMessage(
        role="assistant",
        content="I'll swap Tuesday's meal for you.",
        tool_calls=tool_calls,
    )

    assert message.role == "assistant"
    assert message.content == "I'll swap Tuesday's meal for you."
    assert message.tool_calls == tool_calls


def test_chat_message_role_validation():
    """Test that ChatMessage role is validated."""
    # Valid roles
    user_msg = ChatMessage(role="user", content="Hello")
    assert user_msg.role == "user"

    assistant_msg = ChatMessage(role="assistant", content="Hi")
    assert assistant_msg.role == "assistant"

    # Invalid role should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        ChatMessage(role="system", content="Invalid")


def test_refinement_session_creation():
    """Test creating a RefinementSession."""
    session = RefinementSession(meal_plan_id="plan_123")

    assert session.id  # UUID generated
    assert session.meal_plan_id == "plan_123"
    assert len(session.messages) == 0


def test_refinement_session_with_messages():
    """Test RefinementSession with messages."""
    messages = [
        ChatMessage(role="user", content="Swap Tuesday"),
        ChatMessage(role="assistant", content="Done!"),
    ]

    session = RefinementSession(
        meal_plan_id="plan_123",
        messages=messages,
    )

    assert len(session.messages) == 2
    assert session.messages[0].role == "user"
    assert session.messages[1].role == "assistant"
