from datetime import datetime, UTC
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.models.recipe import Recipe
from app.models.meal_plan import MealSlot, DayOfWeek


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class RecipeAssignment(BaseModel):
    """Assignment of a recipe to a specific day."""

    day: DayOfWeek
    recipe_id: str
    reasoning: str = Field(description="Why this recipe was chosen for this day")


class PlanAssignments(BaseModel):
    """Complete plan with recipe assignments for the week."""

    assignments: list[RecipeAssignment]


SYSTEM_PROMPT = """You are a meal planning expert. Assign recipes to days of the week to create an optimized meal plan.

Your goals (in priority order):
1. **Ingredient efficiency**: Prioritize recipes that use the user's available ingredients
2. **Variety**: Spread different cuisines and protein types across the week
3. **Complexity balance**: Mix simple and complex recipes throughout the week

Guidelines:
- Assign each recipe to at most one day
- You may assign fewer recipes than available days (if recipes don't fit well)
- Consider ingredient overlap between recipes to minimize shopping
- Don't repeat similar dishes on consecutive days
- Provide clear reasoning for each assignment

Example reasoning:
- "Uses chicken and vegetables user already has, good Monday starter"
- "Seafood variety for mid-week, different protein from Monday"
- "Simple pasta dish for busy Friday, uses pantry staples"
"""


class MealPlanGenerator:
    """Generate optimized weekly meal plans from recipe candidates."""

    async def generate(
        self,
        recipes: list[Recipe],
        enabled_days: list[DayOfWeek],
        user_ingredients: list[str],
    ) -> list[MealSlot]:
        """
        Generate meal plan by assigning recipes to days.

        Args:
            recipes: Available recipe candidates
            enabled_days: Days of the week to plan for
            user_ingredients: Ingredients user already has

        Returns:
            List of MealSlot objects with recipe assignments
        """
        if not recipes or not enabled_days:
            return []

        # Build context for LLM
        recipes_text = self._format_recipes(recipes)
        days_text = ", ".join(enabled_days)
        ingredients_text = ", ".join(user_ingredients) if user_ingredients else "none"

        user_prompt = f"""Available recipes:
{recipes_text}

Days to plan: {days_text}
User's ingredients: {ingredients_text}

Assign recipes to days to create an optimal weekly meal plan."""

        try:
            response = await openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=PlanAssignments,
            )

            message = response.choices[0].message
            if message.refusal or message.parsed is None:
                # Fallback to simple round-robin assignment
                return self._fallback_assign(recipes, enabled_days)

            assignments = message.parsed
            return self._build_slots(assignments, recipes, enabled_days)

        except Exception:
            # If LLM fails, use fallback
            return self._fallback_assign(recipes, enabled_days)

    def _format_recipes(self, recipes: list[Recipe]) -> str:
        """Format recipes for LLM prompt."""
        lines = []
        for recipe in recipes:
            ingredients = ", ".join(recipe.extracted_ingredients[:5])  # First 5
            if len(recipe.extracted_ingredients) > 5:
                ingredients += "..."
            lines.append(
                f"- ID: {recipe.id}\n  Title: {recipe.title}\n  Ingredients: {ingredients}"
            )
        return "\n".join(lines)

    def _build_slots(
        self,
        assignments: PlanAssignments,
        recipes: list[Recipe],
        enabled_days: list[DayOfWeek],
    ) -> list[MealSlot]:
        """
        Build MealSlot objects from LLM assignments.

        Validates that:
        - Assigned days are in enabled_days
        - Recipe IDs exist
        - No duplicate recipe assignments
        """
        recipe_ids = {r.id for r in recipes}
        enabled_days_set = set(enabled_days)
        slots = []
        used_recipes = set()

        for assignment in assignments.assignments:
            # Validate day is enabled
            if assignment.day not in enabled_days_set:
                continue

            # Validate recipe exists
            if assignment.recipe_id not in recipe_ids:
                continue

            # Skip if recipe already assigned
            if assignment.recipe_id in used_recipes:
                continue

            # Create slot
            slot = MealSlot(
                day=assignment.day,
                enabled=True,
                recipe_id=assignment.recipe_id,
                assigned_at=datetime.now(UTC),
            )
            slots.append(slot)
            used_recipes.add(assignment.recipe_id)

        return slots

    def _fallback_assign(
        self, recipes: list[Recipe], enabled_days: list[DayOfWeek]
    ) -> list[MealSlot]:
        """
        Simple fallback: round-robin assignment of recipes to days.

        Used when LLM fails or refuses.
        """
        slots = []
        num_to_assign = min(len(recipes), len(enabled_days))

        for i in range(num_to_assign):
            slot = MealSlot(
                day=enabled_days[i],
                enabled=True,
                recipe_id=recipes[i].id,
                assigned_at=datetime.now(UTC),
            )
            slots.append(slot)

        return slots
