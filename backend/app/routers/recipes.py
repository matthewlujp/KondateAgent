from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json

from app.auth import CurrentUser
from app.models.recipe import Recipe
from app.services.recipe_cache import recipe_cache
from app.services.recipe_collection_service import RecipeCollectionService, ProgressEvent

router = APIRouter(prefix="/api/internal/recipes", tags=["recipes"])

# Initialize service
recipe_service = RecipeCollectionService()


# Request/Response models
class RecipeSearchRequest(BaseModel):
    user_id: str = Field(description="User identifier")
    ingredients: list[str] = Field(description="List of ingredient names user has")
    max_results: int = Field(default=15, ge=1, le=30, description="Maximum recipes to return")


class RecipeStreamRequest(BaseModel):
    """Request model for SSE streaming endpoint (user_id comes from JWT)."""

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


@router.post("/search/stream")
async def stream_recipe_search(request: RecipeStreamRequest, current_user: CurrentUser):
    """
    Stream recipe search progress via Server-Sent Events.

    This endpoint provides real-time progress updates as the recipe collection
    pipeline executes. Uses JWT authentication to get user_id.

    SSE Events:
    - progress: Pipeline step progress (ProgressEvent)
    - result: Final scored recipes (list[ScoredRecipeResponse])
    - error: Error message if search fails
    """
    if not request.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")

    # Use asyncio.Queue as bridge between progress callback and SSE stream
    queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(event: ProgressEvent):
        """Progress callback that puts events in queue."""
        await queue.put({"type": "progress", "data": event})

    async def run_search():
        """Run the search pipeline in background task."""
        try:
            scored_recipes = await recipe_service.search_recipes(
                user_id=current_user,
                ingredients=request.ingredients,
                max_results=request.max_results,
                on_progress=on_progress,
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

            # Put result in queue
            await queue.put({"type": "result", "data": response_recipes})

        except Exception as e:
            # Put error in queue
            await queue.put({"type": "error", "data": str(e)})

        finally:
            # Signal completion
            await queue.put(None)

    # Start search task
    asyncio.create_task(run_search())

    async def event_generator():
        """Generate SSE-formatted events from queue."""
        try:
            while True:
                # Get next event from queue
                event = await queue.get()

                # None signals completion
                if event is None:
                    break

                event_type = event["type"]
                event_data = event["data"]

                # Format as SSE
                if event_type == "progress":
                    # Convert ProgressEvent dataclass to dict
                    progress_dict = {
                        "step": event_data.step,
                        "total_steps": event_data.total_steps,
                        "phase": event_data.phase,
                        "message": event_data.message,
                    }
                    yield f"event: progress\ndata: {json.dumps(progress_dict)}\n\n"

                elif event_type == "result":
                    # Convert Pydantic models to dicts
                    result_list = [r.model_dump() for r in event_data]
                    yield f"event: result\ndata: {json.dumps(result_list)}\n\n"

                elif event_type == "error":
                    yield f"event: error\ndata: {json.dumps({'message': event_data})}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
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
