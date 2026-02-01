import pytest

from app.models.meal_plan import MealPlan, MealSlot, ChatMessage, RefinementSession
from app.services.meal_plan_store import MealPlanStore


@pytest.fixture
def store():
    """Create a fresh store for each test."""
    return MealPlanStore()


def test_save_plan(store):
    """Test saving a meal plan."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )

    saved_plan = store.save_plan(plan)

    assert saved_plan.id == plan.id
    assert saved_plan.user_id == "user_123"


def test_get_plan(store):
    """Test retrieving a meal plan by ID."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )
    store.save_plan(plan)

    retrieved = store.get_plan(plan.id)

    assert retrieved is not None
    assert retrieved.id == plan.id
    assert retrieved.user_id == "user_123"


def test_get_nonexistent_plan(store):
    """Test retrieving a non-existent plan returns None."""
    result = store.get_plan("nonexistent_id")
    assert result is None


def test_get_latest_plan_by_user(store):
    """Test retrieving the latest plan for a user."""
    # Create multiple plans for same user
    plan1 = MealPlan(user_id="user_123", ingredient_session_id="session_1")
    plan2 = MealPlan(user_id="user_123", ingredient_session_id="session_2")
    plan3 = MealPlan(user_id="user_456", ingredient_session_id="session_3")

    store.save_plan(plan1)
    store.save_plan(plan2)
    store.save_plan(plan3)

    # Should return the last saved plan for user_123
    latest = store.get_latest_plan_by_user("user_123")
    assert latest is not None
    assert latest.id == plan2.id

    # Should return plan3 for user_456
    latest_456 = store.get_latest_plan_by_user("user_456")
    assert latest_456 is not None
    assert latest_456.id == plan3.id


def test_get_latest_plan_no_plans(store):
    """Test getting latest plan when user has no plans."""
    result = store.get_latest_plan_by_user("nonexistent_user")
    assert result is None


def test_update_slot_recipe(store):
    """Test updating a slot's recipe."""
    slot = MealSlot(day="monday", recipe_id="recipe_1")
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        slots=[slot],
    )
    store.save_plan(plan)

    updated_plan = store.update_slot_recipe(plan.id, slot.id, "recipe_2")

    assert updated_plan is not None
    assert updated_plan.slots[0].recipe_id == "recipe_2"
    assert updated_plan.slots[0].swap_count == 1  # Incremented


def test_update_slot_recipe_multiple_swaps(store):
    """Test that swap_count increments correctly."""
    slot = MealSlot(day="monday", recipe_id="recipe_1", swap_count=2)
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
        slots=[slot],
    )
    store.save_plan(plan)

    updated_plan = store.update_slot_recipe(plan.id, slot.id, "recipe_3")

    assert updated_plan is not None
    assert updated_plan.slots[0].recipe_id == "recipe_3"
    assert updated_plan.slots[0].swap_count == 3


def test_update_slot_recipe_invalid_plan(store):
    """Test updating slot with invalid plan ID returns None."""
    result = store.update_slot_recipe("nonexistent_plan", "slot_id", "recipe_id")
    assert result is None


def test_update_slot_recipe_invalid_slot(store):
    """Test updating nonexistent slot returns None."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )
    store.save_plan(plan)

    result = store.update_slot_recipe(plan.id, "nonexistent_slot", "recipe_id")
    assert result is None


def test_get_or_create_refinement_session(store):
    """Test getting or creating a refinement session."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )
    store.save_plan(plan)

    # First call should create
    session = store.get_or_create_refinement_session(plan.id)
    assert session is not None
    assert session.meal_plan_id == plan.id
    assert len(session.messages) == 0

    # Second call should return same session
    session2 = store.get_or_create_refinement_session(plan.id)
    assert session2 is not None
    assert session2.id == session.id


def test_get_or_create_refinement_session_invalid_plan(store):
    """Test creating session for nonexistent plan returns None."""
    result = store.get_or_create_refinement_session("nonexistent_plan")
    assert result is None


def test_add_message(store):
    """Test adding messages to a refinement session."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )
    store.save_plan(plan)

    session = store.get_or_create_refinement_session(plan.id)
    assert session is not None

    message = ChatMessage(role="user", content="Swap Tuesday")
    updated_session = store.add_message(session.id, message)

    assert updated_session is not None
    assert len(updated_session.messages) == 1
    assert updated_session.messages[0].content == "Swap Tuesday"


def test_add_multiple_messages(store):
    """Test adding multiple messages."""
    plan = MealPlan(
        user_id="user_123",
        ingredient_session_id="session_456",
    )
    store.save_plan(plan)

    session = store.get_or_create_refinement_session(plan.id)
    assert session is not None

    msg1 = ChatMessage(role="user", content="Message 1")
    msg2 = ChatMessage(role="assistant", content="Message 2")
    msg3 = ChatMessage(role="user", content="Message 3")

    store.add_message(session.id, msg1)
    store.add_message(session.id, msg2)
    updated_session = store.add_message(session.id, msg3)

    assert updated_session is not None
    assert len(updated_session.messages) == 3
    assert updated_session.messages[0].content == "Message 1"
    assert updated_session.messages[1].content == "Message 2"
    assert updated_session.messages[2].content == "Message 3"


def test_add_message_invalid_session(store):
    """Test adding message to nonexistent session returns None."""
    message = ChatMessage(role="user", content="Test")
    result = store.add_message("nonexistent_session", message)
    assert result is None
