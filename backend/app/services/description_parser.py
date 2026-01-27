from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class ParsedRecipeIngredients(BaseModel):
    """Structured ingredient extraction from recipe description."""

    ingredients: list[str] = Field(
        description="List of ingredients mentioned in the recipe"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that this is a recipe (0.0-1.0)",
    )


SYSTEM_PROMPT = """You are a recipe ingredient extractor. Extract ingredients from video titles and descriptions.

Rules:
- Extract all ingredients mentioned (e.g., "chicken breast", "olive oil", "garlic")
- Normalize ingredient names (e.g., "2 cloves garlic" → "garlic")
- Keep specific varieties (e.g., "cherry tomatoes" not just "tomatoes")
- Ignore cooking equipment, techniques, or non-food items
- Set confidence based on how clearly this is a recipe:
  - 0.9-1.0: Clear recipe with detailed ingredients
  - 0.5-0.8: Recipe but ingredients are vague or incomplete
  - 0.0-0.4: Not a recipe or no ingredients mentioned

If this is clearly not a recipe (e.g., vlog, review, unrelated content), return empty ingredients list with low confidence."""


class DescriptionParser:
    """Parse recipe ingredients from video/post descriptions using LLM."""

    async def parse(self, title: str, description: str) -> ParsedRecipeIngredients:
        """
        Extract ingredients from a video/post title and description.

        Args:
            title: Video/post title
            description: Full description text

        Returns:
            ParsedRecipeIngredients with ingredients list and confidence score

        Example:
            >>> parser = DescriptionParser()
            >>> result = await parser.parse(
            ...     "Easy Chicken Pasta Recipe",
            ...     "Ingredients: 2 chicken breasts, 1 lb pasta, 3 tomatoes, 2 cloves garlic..."
            ... )
            >>> result.ingredients
            ["chicken breast", "pasta", "tomatoes", "garlic"]
            >>> result.confidence
            0.95
        """
        # Combine title and description for context
        combined_text = f"Title: {title}\n\nDescription: {description}"

        # Truncate if too long (keep first 2000 chars)
        if len(combined_text) > 2000:
            combined_text = combined_text[:2000] + "..."

        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": combined_text},
            ],
            response_format=ParsedRecipeIngredients,
        )

        message = response.choices[0].message
        if message.refusal or message.parsed is None:
            # Return empty result if parsing fails
            return ParsedRecipeIngredients(ingredients=[], confidence=0.0)

        return message.parsed

    async def parse_batch(
        self, recipes: list[tuple[str, str]]
    ) -> list[ParsedRecipeIngredients]:
        """
        Parse multiple recipe descriptions in parallel.

        Args:
            recipes: List of (title, description) tuples

        Returns:
            List of ParsedRecipeIngredients in same order as input
        """
        import asyncio

        tasks = [self.parse(title, description) for title, description in recipes]
        return await asyncio.gather(*tasks)
