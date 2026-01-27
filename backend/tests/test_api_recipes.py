import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC, timedelta

from app.main import app
from app.models.recipe import Recipe
from app.services.recipe_matcher import RecipeMatchScore
from app.services.recipe_collection_service import ScoredRecipe


class TestRecipeSearchEndpoint:
    """Tests for POST /api/internal/recipes/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_recipes_success(self):
        """Test successful recipe search."""
        now = datetime.now(UTC)

        # Mock recipe and score
        mock_recipe = Recipe(
            source="youtube",
            source_id="video123",
            url="https://youtube.com/watch?v=video123",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Chicken Pasta Recipe",
            creator_name="Chef's Kitchen",
            creator_id="UCchannel",
            extracted_ingredients=["chicken", "pasta", "tomatoes", "garlic"],
            raw_description="Recipe description",
            duration="PT10M",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )

        mock_scored_recipe = ScoredRecipe(
            recipe=mock_recipe,
            score=RecipeMatchScore(
                coverage_score=0.85,
                missing_ingredients=["basil"],
                reasoning="User has all main ingredients",
            ),
        )

        with patch("app.routers.recipes.recipe_service.search_recipes", return_value=[mock_scored_recipe]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": "user123",
                        "ingredients": ["chicken", "pasta", "tomatoes"],
                        "max_results": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["recipes"]) == 1
                assert data["recipes"][0]["recipe"]["title"] == "Chicken Pasta Recipe"
                assert data["recipes"][0]["coverage_score"] == 0.85
                assert "basil" in data["recipes"][0]["missing_ingredients"]

    @pytest.mark.asyncio
    async def test_search_recipes_empty_ingredients(self):
        """Test search with empty ingredients returns 400."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/internal/recipes/search",
                json={
                    "user_id": "user123",
                    "ingredients": [],
                    "max_results": 10,
                },
            )

            assert response.status_code == 400
            assert "No ingredients provided" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_search_recipes_service_failure(self):
        """Test handling of service failure."""
        with patch("app.routers.recipes.recipe_service.search_recipes", side_effect=Exception("Service error")):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": "user123",
                        "ingredients": ["chicken"],
                        "max_results": 10,
                    },
                )

                assert response.status_code == 500
                assert "Recipe search failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_search_recipes_default_max_results(self):
        """Test that default max_results is used."""
        with patch("app.routers.recipes.recipe_service.search_recipes", return_value=[]) as mock_search:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": "user123",
                        "ingredients": ["chicken"],
                    },
                )

                assert response.status_code == 200
                # Verify default max_results=15 was used
                call_args = mock_search.call_args
                assert call_args[1]["max_results"] == 15

    @pytest.mark.asyncio
    async def test_search_recipes_max_results_limit(self):
        """Test that max_results is capped at 30."""
        with patch("app.routers.recipes.recipe_service.search_recipes", return_value=[]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": "user123",
                        "ingredients": ["chicken"],
                        "max_results": 100,  # Over limit
                    },
                )

                # Should be accepted but validated by Pydantic
                assert response.status_code == 422  # Validation error


class TestGetRecipeEndpoint:
    """Tests for GET /api/internal/recipes/{recipe_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_recipe_success(self):
        """Test retrieving a cached recipe."""
        now = datetime.now(UTC)

        mock_recipe = Recipe(
            source="youtube",
            source_id="video123",
            url="https://youtube.com/watch?v=video123",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Test Recipe",
            creator_name="Chef",
            creator_id="UCchannel",
            extracted_ingredients=["chicken", "rice"],
            raw_description="Description",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )

        with patch("app.routers.recipes.recipe_cache.get", return_value=mock_recipe):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/internal/recipes/{mock_recipe.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == mock_recipe.id
                assert data["title"] == "Test Recipe"

    @pytest.mark.asyncio
    async def test_get_recipe_not_found(self):
        """Test retrieving non-existent recipe."""
        with patch("app.routers.recipes.recipe_cache.get", return_value=None):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/internal/recipes/nonexistent-id")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_recipe_expired(self):
        """Test that expired recipes return 404."""
        with patch("app.routers.recipes.recipe_cache.get", return_value=None):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/internal/recipes/expired-id")

                assert response.status_code == 404
