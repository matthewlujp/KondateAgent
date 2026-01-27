from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.recipe import Recipe
from app.services.recipe_cache import recipe_cache
from app.services.recipe_collection_service import RecipeCollectionService

router = APIRouter(prefix="/api/internal/recipes", tags=["recipes"])

# Initialize service
recipe_service = RecipeCollectionService()


# Request/Response models
class RecipeSearchRequest(BaseModel):
    user_id: str = Field(description="User identifier")
    ingredients: list[str] = Field(description="List of ingredient names user has")
    max_results: int = Field(default=15, ge=1, le=30, description="Maximum recipes to return")


class ScoredRecipeResponse(BaseModel):
    """Recipe with match score for API response."""

    recipe: Recipe
    coverage_score: float = Field(ge=0.0, le=1.0, description="Match score 0-1")
    missing_ingredients: list[str] = Field(description="Ingredients user needs to buy")
    reasoning: str = Field(description="Why this recipe matches")


class RecipeSearchResponse(BaseModel):
    recipes: list[ScoredRecipeResponse]


# Endpoints
@router.post("/search", response_model=RecipeSearchResponse)
async def search_recipes(request: RecipeSearchRequest):
    """
    Search for recipes matching user's ingredients.

    This is an internal endpoint called by the Meal Plan Generator.
    It orchestrates the full recipe collection pipeline.

    Returns scored recipes ordered by match quality (best first).
    """
    if not request.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")

    try:
        scored_recipes = await recipe_service.search_recipes(
            user_id=request.user_id,
            ingredients=request.ingredients,
            max_results=request.max_results,
        )

        # Convert to response format
        response_recipes = [
            ScoredRecipeResponse(
                recipe=sr.recipe,
                coverage_score=sr.score.coverage_score,
                missing_ingredients=sr.score.missing_ingredients,
                reasoning=sr.score.reasoning,
            )
            for sr in scored_recipes
        ]

        return RecipeSearchResponse(recipes=response_recipes)

    except Exception as e:
        # Log error in production
        raise HTTPException(
            status_code=500,
            detail=f"Recipe search failed: {str(e)}",
        )


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str):
    """
    Retrieve a cached recipe by ID.

    This is an internal endpoint for retrieving recipe details
    after the meal planner has selected recipes.
    """
    recipe = recipe_cache.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found or expired")
    return recipe


@router.post("/parse", response_model=Recipe)
async def parse_recipe(source: str, source_id: str, description: str):
    """
    Parse a recipe from external source.

    This is an internal endpoint for ad-hoc recipe parsing.
    Used when the meal planner needs to process a specific recipe URL.
    """
    # This is a placeholder - full implementation would:
    # 1. Validate source (youtube/instagram)
    # 2. Fetch details from API if needed
    # 3. Parse description
    # 4. Create and cache Recipe
    # For now, raise not implemented
    raise HTTPException(status_code=501, detail="Not implemented yet")
