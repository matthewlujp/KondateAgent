from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class RecipeMatchScore(BaseModel):
    """Structured match score for a recipe against user ingredients."""

    coverage_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of recipe ingredients user already has (0.0-1.0)",
    )
    missing_ingredients: list[str] = Field(
        description="Ingredients user needs to buy"
    )
    reasoning: str = Field(
        description="Brief explanation of the match quality"
    )


SYSTEM_PROMPT = """You are a recipe matching expert. Score how well a recipe matches user's available ingredients.

Your task:
1. Calculate coverage_score: What percentage of recipe ingredients does the user have?
   - Consider ingredient substitutions (e.g., chicken breast ≈ chicken thigh)
   - Consider forms (e.g., canned tomatoes ≈ fresh tomatoes)
   - Basic pantry items (salt, pepper, oil) don't reduce score if missing
2. List missing_ingredients: What must the user buy?
   - Only include significant ingredients (not salt, pepper, basic spices)
   - Use the recipe's ingredient names
3. Provide reasoning: Brief explanation (1-2 sentences)

Examples:
- User has all main ingredients, missing only garnish → score: 0.85-0.95
- User has protein and 2/3 vegetables → score: 0.65-0.75
- User has only 1 ingredient → score: 0.10-0.30"""


class RecipeMatcher:
    """Match and score recipes against user's available ingredients."""

    async def score(
        self,
        user_ingredients: list[str],
        recipe_ingredients: list[str],
    ) -> RecipeMatchScore:
        """
        Score how well a recipe matches user's ingredients.

        Args:
            user_ingredients: List of ingredients user has
            recipe_ingredients: List of ingredients recipe requires

        Returns:
            RecipeMatchScore with coverage_score, missing_ingredients, and reasoning

        Example:
            >>> matcher = RecipeMatcher()
            >>> score = await matcher.score(
            ...     ["chicken breast", "tomatoes", "garlic", "pasta"],
            ...     ["chicken breast", "tomatoes", "garlic", "pasta", "basil", "parmesan"]
            ... )
            >>> score.coverage_score
            0.80
            >>> score.missing_ingredients
            ["basil", "parmesan"]
        """
        if not recipe_ingredients:
            # No ingredients listed = can't match
            return RecipeMatchScore(
                coverage_score=0.0,
                missing_ingredients=[],
                reasoning="Recipe has no ingredients listed",
            )

        user_text = ", ".join(user_ingredients) if user_ingredients else "none"
        recipe_text = ", ".join(recipe_ingredients)

        user_prompt = f"""User's ingredients: {user_text}
Recipe requires: {recipe_text}"""

        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=RecipeMatchScore,
        )

        message = response.choices[0].message
        if message.refusal or message.parsed is None:
            # Fallback: simple exact match scoring
            return self._fallback_score(user_ingredients, recipe_ingredients)

        return message.parsed

    async def score_batch(
        self,
        user_ingredients: list[str],
        recipes: list[tuple[str, list[str]]],  # (recipe_id, ingredients)
    ) -> dict[str, RecipeMatchScore]:
        """
        Score multiple recipes in parallel.

        Args:
            user_ingredients: User's available ingredients
            recipes: List of (recipe_id, recipe_ingredients) tuples

        Returns:
            Dict mapping recipe_id to RecipeMatchScore
        """
        import asyncio

        tasks = {
            recipe_id: self.score(user_ingredients, ingredients)
            for recipe_id, ingredients in recipes
        }

        # Execute all scoring tasks in parallel
        results = await asyncio.gather(*tasks.values())

        return dict(zip(tasks.keys(), results))

    def _fallback_score(
        self,
        user_ingredients: list[str],
        recipe_ingredients: list[str],
    ) -> RecipeMatchScore:
        """
        Simple fallback scoring if LLM fails.

        Uses exact string matching (case-insensitive).
        """
        if not recipe_ingredients:
            return RecipeMatchScore(
                coverage_score=0.0,
                missing_ingredients=[],
                reasoning="No recipe ingredients to match",
            )

        # Normalize for matching
        user_set = {ing.lower().strip() for ing in user_ingredients}
        recipe_list = [ing.strip() for ing in recipe_ingredients]

        matched = 0
        missing = []

        for recipe_ing in recipe_list:
            recipe_ing_lower = recipe_ing.lower()
            # Check if user has this ingredient (exact match or substring)
            has_ingredient = any(
                user_ing in recipe_ing_lower or recipe_ing_lower in user_ing
                for user_ing in user_set
            )

            if has_ingredient:
                matched += 1
            else:
                missing.append(recipe_ing)

        coverage = matched / len(recipe_list) if recipe_list else 0.0

        return RecipeMatchScore(
            coverage_score=round(coverage, 2),
            missing_ingredients=missing,
            reasoning=f"Simple match: {matched}/{len(recipe_list)} ingredients available",
        )
