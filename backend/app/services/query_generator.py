from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class SearchQueries(BaseModel):
    """Structured search queries from LLM."""

    direct_queries: list[str]  # Ingredient combination queries
    dish_suggestions: list[str]  # Specific dish name suggestions


# Language-specific system prompts
SYSTEM_PROMPTS = {
    "en": """You are a recipe search query generator. Given a list of ingredients, generate search queries for finding recipes.

Generate two types of queries:
1. Direct queries: Combine 2-4 ingredients into recipe search terms (e.g., "chicken tomato pasta recipe")
2. Dish suggestions: Suggest specific dish names that use these ingredients (e.g., "chicken pomodoro", "garlic butter pasta")

Rules:
- Generate 3-5 direct queries using different ingredient combinations
- Generate 3-5 dish suggestions (real dish names, not made up)
- Focus on common, popular dishes that match the ingredients
- Be creative but realistic
- Prioritize main ingredients over secondary ones
- ALL queries MUST be in English""",

    "ja": """あなたはレシピ検索クエリ生成器です。食材リストから、レシピを検索するためのクエリを生成してください。

2種類のクエリを生成してください：
1. 直接クエリ：2〜4つの食材を組み合わせたレシピ検索語（例：「鶏肉 トマト パスタ レシピ」）
2. 料理提案：これらの食材を使う具体的な料理名（例：「チキンポモドーロ」、「鶏の照り焼き」）

ルール：
- 異なる食材の組み合わせで3〜5つの直接クエリを生成
- 3〜5つの料理提案を生成（実在する料理名のみ）
- 一般的で人気のある料理に焦点を当てる
- 創造的かつ現実的に
- 主要な食材を優先する
- すべてのクエリは必ず日本語で書いてください""",
}

# Default prompt when language not specified
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPTS["en"]


class QueryGenerator:
    """Generate search queries from user ingredients using LLM."""

    async def generate(
        self,
        ingredients: list[str],
        languages: Optional[list[str]] = None,
    ) -> SearchQueries:
        """
        Generate search queries from ingredient list.

        Args:
            ingredients: List of ingredient names
            languages: Target languages for queries (e.g., ['en'], ['ja'], or ['en', 'ja'])
                      If multiple languages, generates queries in the primary (first) language

        Returns:
            SearchQueries with direct_queries and dish_suggestions

        Example:
            >>> generator = QueryGenerator()
            >>> queries = await generator.generate(["chicken", "tomatoes"], languages=["ja"])
            >>> queries.direct_queries
            ["鶏肉 トマト レシピ", "チキン トマト煮込み"]
        """
        if not ingredients:
            return SearchQueries(direct_queries=[], dish_suggestions=[])

        # Determine which language to use for query generation
        # Use the first language in the list as primary
        primary_language = languages[0] if languages and len(languages) > 0 else "en"

        # Get appropriate system prompt for language
        system_prompt = SYSTEM_PROMPTS.get(primary_language, DEFAULT_SYSTEM_PROMPT)

        ingredient_text = ", ".join(ingredients)

        # Format user prompt based on language
        if primary_language == "ja":
            user_prompt = f"食材: {ingredient_text}"
        else:
            user_prompt = f"Ingredients: {ingredient_text}"

        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SearchQueries,
        )

        message = response.choices[0].message
        if message.refusal or message.parsed is None:
            # Fallback: generate basic queries from ingredients
            return self._fallback_queries(ingredients, primary_language)

        return message.parsed

    def _fallback_queries(self, ingredients: list[str], language: str = "en") -> SearchQueries:
        """
        Generate fallback queries if LLM fails.

        Creates simple combination queries from ingredients.

        Args:
            ingredients: List of ingredient names
            language: Target language for queries
        """
        direct_queries = []

        # Language-specific recipe suffix
        recipe_suffix = "レシピ" if language == "ja" else "recipe"

        # Generate queries with 2-3 ingredient combinations
        if len(ingredients) >= 2:
            # Take first 2 main ingredients
            direct_queries.append(f"{ingredients[0]} {ingredients[1]} {recipe_suffix}")

        if len(ingredients) >= 3:
            # Take first 3 ingredients
            direct_queries.append(f"{ingredients[0]} {ingredients[1]} {ingredients[2]} {recipe_suffix}")

        # Add single ingredient query for main ingredient
        if ingredients:
            direct_queries.append(f"{ingredients[0]} {recipe_suffix}")

        return SearchQueries(
            direct_queries=direct_queries[:5],  # Limit to 5
            dish_suggestions=[],  # Can't generate creative suggestions without LLM
        )
