from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth import CurrentUser
from app.models.meal_plan import MealPlan, DayOfWeek, MealSlot, ChatMessage
from app.services.session_store import session_store
from app.services.recipe_cache import recipe_cache
from app.services.meal_plan_store import meal_plan_store
from app.services.meal_plan_generator import MealPlanGenerator
from app.services.meal_plan_refinement import MealPlanRefinementAgent


router = APIRouter(prefix="/api/meal-plans", tags=["meal-plans"])

# Initialize services
generator = MealPlanGenerator()
refinement_agent = MealPlanRefinementAgent()


# Day order for sorting
DAY_ORDER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# Request/Response models
class GeneratePlanRequest(BaseModel):
    ingredient_session_id: str
    enabled_days: list[DayOfWeek]
    recipe_ids: list[str]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    response: str
    plan: MealPlan
    tool_calls: list[dict]


# Endpoints
@router.post("", response_model=MealPlan, status_code=201)
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: CurrentUser,
):
    """Generate a new meal plan from recipes and enabled days."""
    # Validate ingredient session exists and belongs to user
    session = session_store.get_session(request.ingredient_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Ingredient session not found")

    if session.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot create plan for another user's session",
        )

    # Resolve recipe_ids from cache
    recipes = []
    for recipe_id in request.recipe_ids:
        recipe = recipe_cache.get(recipe_id)
        if recipe:
            recipes.append(recipe)

    if not recipes:
        raise HTTPException(status_code=400, detail="No valid recipes provided")

    # Get user ingredients for context
    user_ingredients = [ing.name for ing in session.ingredients]

    # Generate meal slots
    generated_slots = await generator.generate(
        recipes=recipes,
        enabled_days=request.enabled_days,
        user_ingredients=user_ingredients,
    )

    # Add disabled day slots for non-enabled days
    all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    enabled_set = set(request.enabled_days)
    assigned_days = {slot.day for slot in generated_slots}

    all_slots = list(generated_slots)

    # Add disabled slots for days not enabled
    for day in all_days:
        if day not in enabled_set and day not in assigned_days:
            all_slots.append(MealSlot(day=day, enabled=False))

    # Sort slots by day order (Monday-Sunday)
    all_slots.sort(key=lambda s: DAY_ORDER[s.day])

    # Create and save plan
    plan = MealPlan(
        user_id=current_user,
        ingredient_session_id=request.ingredient_session_id,
        status="active",
        slots=all_slots,
    )

    meal_plan_store.save_plan(plan)
    return plan


@router.get("/{plan_id}", response_model=MealPlan)
async def get_plan(plan_id: str, current_user: CurrentUser):
    """Get an existing meal plan by ID."""
    plan = meal_plan_store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    # Verify ownership
    if plan.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's meal plan",
        )

    return plan


@router.post("/{plan_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    plan_id: str,
    request: ChatRequest,
    current_user: CurrentUser,
):
    """Send a chat message to refine the meal plan."""
    # Get plan and verify ownership
    plan = meal_plan_store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    if plan.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's meal plan",
        )

    # Get or create refinement session
    refinement_session = meal_plan_store.get_or_create_refinement_session(plan_id)
    if not refinement_session:
        raise HTTPException(status_code=500, detail="Failed to create refinement session")

    # Build recipe pool from cache
    recipe_pool = []
    # Get all recipes from session's ingredient session
    session = session_store.get_session(plan.ingredient_session_id)
    if session:
        # Get recipes from cache (simplified: get all cached recipes)
        # In production, filter by session's recipe search results
        recipe_pool = list(recipe_cache._recipes.values())

    # Build chat history
    chat_history = refinement_session.messages

    # Add user message to history
    user_message = ChatMessage(role="user", content=request.message)
    meal_plan_store.add_message(refinement_session.id, user_message)

    # Process message with agent
    response_text, tool_calls = await refinement_agent.process_message(
        message=request.message,
        plan=plan,
        recipe_pool=recipe_pool,
        chat_history=chat_history,
    )

    # Add assistant message to history
    assistant_message = ChatMessage(
        role="assistant",
        content=response_text,
        tool_calls=tool_calls if tool_calls else None,
    )
    meal_plan_store.add_message(refinement_session.id, assistant_message)

    # Save updated plan
    meal_plan_store.save_plan(plan)

    return ChatResponse(
        response=response_text,
        plan=plan,
        tool_calls=tool_calls,
    )
