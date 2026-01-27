from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class SearchQueries(BaseModel):
    """Structured search queries from LLM."""

    direct_queries: list[str]  # Ingredient combination queries
    dish_suggestions: list[str]  # Specific dish name suggestions


SYSTEM_PROMPT = """You are a recipe search query generator. Given a list of ingredients, generate search queries for finding recipes.

Generate two types of queries:
1. Direct queries: Combine 2-4 ingredients into recipe search terms (e.g., "chicken tomato pasta recipe")
2. Dish suggestions: Suggest specific dish names that use these ingredients (e.g., "chicken pomodoro", "garlic butter pasta")

Rules:
- Generate 3-5 direct queries using different ingredient combinations
- Generate 3-5 dish suggestions (real dish names, not made up)
- Focus on common, popular dishes that match the ingredients
- Be creative but realistic
- Prioritize main ingredients over secondary ones"""


class QueryGenerator:
    """Generate search queries from user ingredients using LLM."""

    async def generate(self, ingredients: list[str]) -> SearchQueries:
        """
        Generate search queries from ingredient list.

        Args:
            ingredients: List of ingredient names

        Returns:
            SearchQueries with direct_queries and dish_suggestions

        Example:
            >>> generator = QueryGenerator()
            >>> queries = await generator.generate(["chicken", "tomatoes", "garlic", "pasta"])
            >>> queries.direct_queries
            ["chicken tomato pasta recipe", "garlic chicken recipe"]
            >>> queries.dish_suggestions
            ["chicken pomodoro", "garlic butter chicken pasta"]
        """
        if not ingredients:
            return SearchQueries(direct_queries=[], dish_suggestions=[])

        ingredient_text = ", ".join(ingredients)
        user_prompt = f"Ingredients: {ingredient_text}"

        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SearchQueries,
        )

        message = response.choices[0].message
        if message.refusal or message.parsed is None:
            # Fallback: generate basic queries from ingredients
            return self._fallback_queries(ingredients)

        return message.parsed

    def _fallback_queries(self, ingredients: list[str]) -> SearchQueries:
        """
        Generate fallback queries if LLM fails.

        Creates simple combination queries from ingredients.
        """
        direct_queries = []

        # Generate queries with 2-3 ingredient combinations
        if len(ingredients) >= 2:
            # Take first 2 main ingredients
            direct_queries.append(f"{ingredients[0]} {ingredients[1]} recipe")

        if len(ingredients) >= 3:
            # Take first 3 ingredients
            direct_queries.append(f"{ingredients[0]} {ingredients[1]} {ingredients[2]} recipe")

        # Add single ingredient query for main ingredient
        if ingredients:
            direct_queries.append(f"{ingredients[0]} recipe")

        return SearchQueries(
            direct_queries=direct_queries[:5],  # Limit to 5
            dish_suggestions=[],  # Can't generate creative suggestions without LLM
        )
