from dataclasses import dataclass
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.models.recipe import Recipe
from app.models.meal_plan import MealPlan, ChatMessage, DayOfWeek


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


@dataclass
class SwapResult:
    """Result of a meal swap operation."""

    success: bool
    day: Optional[str]
    old_recipe_id: Optional[str]
    new_recipe_id: Optional[str]
    message: str


class SwapDecision(BaseModel):
    """LLM decision about whether to swap a meal."""

    should_swap: bool = Field(description="Whether to perform a swap")
    day: Optional[DayOfWeek] = Field(
        default=None, description="Day to swap (if should_swap is True)"
    )
    criteria: Optional[str] = Field(
        default=None, description="Criteria for choosing alternative recipe"
    )
    selected_recipe_id: Optional[str] = Field(
        default=None,
        description="ID of the recipe to swap to, chosen from available alternatives based on criteria",
    )
    response_text: str = Field(description="Natural language response to the user")


SYSTEM_PROMPT = """You are a helpful meal planning assistant. Users can ask you to modify their weekly meal plan through natural conversation.

Available tool: swap_meal
- Replaces a meal on a specific day with an alternative recipe
- Use when user wants to change a specific day's meal
- Examples: "swap Tuesday", "change Monday to something lighter", "I don't like Wednesday's meal"

Your task:
1. Understand what the user wants
2. Decide if they're asking for a swap (set should_swap=True/False)
3. If swapping:
   - Identify the day to swap
   - Extract criteria for the new recipe (e.g., "lighter", "vegetarian", "different protein", "Japanese", "quick")
   - IMPORTANT: Select the best matching recipe from the available alternatives list based on the criteria
   - Set selected_recipe_id to the ID of the chosen recipe that best matches the user's request
4. Provide a friendly response

When selecting a recipe:
- Match the user's criteria (cuisine type, cooking time, dietary preferences, etc.)
- Look at recipe titles and descriptions to identify cuisine/style
- If user asks for "Japanese", choose a recipe with Japanese dish name or description
- If user asks for "quick", choose simpler recipes with fewer ingredients

If user asks general questions or gives feedback without requesting changes, respond conversationally without swapping.

Examples:
- User: "Can you swap Tuesday for something lighter?" → should_swap=True, day="tuesday", criteria="lighter meal", selected_recipe_id="<id of lightest recipe>"
- User: "Change Monday to Japanese" → should_swap=True, day="monday", criteria="Japanese cuisine", selected_recipe_id="<id of Japanese recipe>"
- User: "I don't like fish" → should_swap=False, response="I'll keep that in mind for future plans!"
- User: "This looks great!" → should_swap=False, response="Glad you like it!"
"""


class MealPlanRefinementAgent:
    """Agent for refining meal plans through chat-based swaps."""

    def execute_swap(
        self,
        plan: MealPlan,
        day: DayOfWeek,
        recipe_pool: list[Recipe],
        criteria: Optional[str],
        selected_recipe_id: Optional[str] = None,
    ) -> SwapResult:
        """
        Execute a meal swap for a specific day.

        Finds an alternative recipe that:
        - Is not already assigned to any day in the plan
        - Is different from the current recipe
        - Matches the selected_recipe_id if provided by LLM

        Args:
            plan: Current meal plan
            day: Day to swap
            recipe_pool: Available recipes to choose from
            criteria: Optional criteria for choosing recipe
            selected_recipe_id: Optional recipe ID selected by LLM based on criteria

        Returns:
            SwapResult with success status and details
        """
        # Find the slot for this day
        target_slot = None
        for slot in plan.slots:
            if slot.day == day and slot.enabled:
                target_slot = slot
                break

        if not target_slot:
            return SwapResult(
                success=False,
                day=day,
                old_recipe_id=None,
                new_recipe_id=None,
                message=f"No meal planned for {day}",
            )

        # Get currently assigned recipe IDs
        assigned_recipe_ids = {
            slot.recipe_id for slot in plan.slots if slot.recipe_id is not None
        }

        # Find available alternatives (not currently assigned)
        available_recipes = [
            recipe
            for recipe in recipe_pool
            if recipe.id not in assigned_recipe_ids
        ]

        if not available_recipes:
            return SwapResult(
                success=False,
                day=day,
                old_recipe_id=target_slot.recipe_id,
                new_recipe_id=None,
                message=f"No alternative recipes available for {day}",
            )

        # Use LLM-selected recipe if provided and valid
        new_recipe = None
        if selected_recipe_id:
            for recipe in available_recipes:
                if recipe.id == selected_recipe_id:
                    new_recipe = recipe
                    break

        # Fallback to first available if LLM selection not found
        if new_recipe is None:
            new_recipe = available_recipes[0]

        old_recipe_id = target_slot.recipe_id

        return SwapResult(
            success=True,
            day=day,
            old_recipe_id=old_recipe_id,
            new_recipe_id=new_recipe.id,
            message=f"Swapped {day}'s meal to {new_recipe.title}",
        )

    async def process_message(
        self,
        message: str,
        plan: MealPlan,
        recipe_pool: list[Recipe],
        chat_history: list[ChatMessage],
    ) -> tuple[str, list[dict]]:
        """
        Process a user message and optionally execute a swap.

        Args:
            message: User's message
            plan: Current meal plan
            recipe_pool: Available recipes
            chat_history: Previous conversation messages

        Returns:
            Tuple of (response_text, tool_calls)
            - response_text: Natural language response to user
            - tool_calls: List of tool call dicts (empty if no swap)
        """
        decision = await self._invoke_agent(message, plan, recipe_pool, chat_history)

        if not decision.should_swap:
            return decision.response_text, []

        # Execute the swap
        swap_result = self.execute_swap(
            plan=plan,
            day=decision.day,
            recipe_pool=recipe_pool,
            criteria=decision.criteria,
            selected_recipe_id=decision.selected_recipe_id,
        )

        if swap_result.success:
            # Update the plan's slot
            for slot in plan.slots:
                if slot.day == decision.day:
                    slot.recipe_id = swap_result.new_recipe_id
                    slot.swap_count += 1
                    break

            # Create tool call record
            tool_call = {
                "id": f"call_swap_{decision.day}",
                "type": "function",
                "function": {
                    "name": "swap_meal",
                    "arguments": f'{{"day": "{decision.day}", "old_recipe": "{swap_result.old_recipe_id}", "new_recipe": "{swap_result.new_recipe_id}"}}',
                },
            }

            response = f"{decision.response_text}\n\n{swap_result.message}"
            return response, [tool_call]
        else:
            # Swap failed
            return f"{decision.response_text}\n\n{swap_result.message}", []

    async def _invoke_agent(
        self,
        message: str,
        plan: MealPlan,
        recipe_pool: list[Recipe],
        chat_history: list[ChatMessage],
    ) -> SwapDecision:
        """
        Invoke LLM to decide on action.

        Args:
            message: User's current message
            plan: Current meal plan
            recipe_pool: Available recipes
            chat_history: Previous messages

        Returns:
            SwapDecision with LLM's decision
        """
        # Build context about current plan
        plan_text = self._format_plan(plan, recipe_pool)
        available_recipes_text = self._format_available_recipes(plan, recipe_pool)

        # Build message history for LLM
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add context about current plan
        context_message = f"""Current meal plan:
{plan_text}

Available alternative recipes:
{available_recipes_text}"""

        messages.append({"role": "system", "content": context_message})

        # Add chat history
        for msg in chat_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": message})

        try:
            response = await openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=SwapDecision,
            )

            parsed_message = response.choices[0].message
            if parsed_message.refusal or parsed_message.parsed is None:
                # Fallback: don't swap
                return SwapDecision(
                    should_swap=False,
                    response_text="I understand. Let me know if you'd like to make any changes!",
                )

            return parsed_message.parsed

        except Exception:
            # Fallback on error
            return SwapDecision(
                should_swap=False,
                response_text="I'm having trouble understanding. Could you rephrase that?",
            )

    def _format_plan(self, plan: MealPlan, recipe_pool: list[Recipe]) -> str:
        """Format current plan for LLM."""
        recipe_map = {r.id: r for r in recipe_pool}
        lines = []
        for slot in plan.slots:
            if slot.enabled and slot.recipe_id:
                recipe = recipe_map.get(slot.recipe_id)
                if recipe:
                    lines.append(f"- {slot.day.capitalize()}: {recipe.title}")
                else:
                    lines.append(f"- {slot.day.capitalize()}: [Recipe not found]")
        return "\n".join(lines) if lines else "No meals planned yet"

    def _format_available_recipes(
        self, plan: MealPlan, recipe_pool: list[Recipe]
    ) -> str:
        """Format available (unassigned) recipes for LLM with IDs for selection."""
        assigned_ids = {slot.recipe_id for slot in plan.slots if slot.recipe_id}
        available = [r for r in recipe_pool if r.id not in assigned_ids]

        if not available:
            return "No additional recipes available"

        # Include ID, title, and description to help LLM match criteria
        lines = []
        for r in available[:10]:  # Increased limit for better selection
            desc_preview = r.raw_description[:50] + "..." if len(r.raw_description) > 50 else r.raw_description
            lines.append(f"- ID: {r.id} | {r.title} | {desc_preview}")

        if len(available) > 10:
            lines.append(f"... and {len(available) - 10} more")
        return "\n".join(lines)
