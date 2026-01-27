import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC, timedelta

from app.auth import create_access_token
from app.main import app
from app.models.recipe import Recipe, PreferredCreator
from app.services.query_generator import SearchQueries
from app.services.description_parser import ParsedRecipeIngredients
from app.services.recipe_matcher import RecipeMatchScore
from app.services.youtube_client import YouTubeSearchResult
from app.services.instagram_client import InstagramSearchResult


class TestRecipeCollectionE2E:
    """End-to-end integration tests for the full recipe collection flow."""

    @pytest.mark.asyncio
    async def test_full_recipe_collection_flow_with_preferred_creator(self):
        """
        Test the complete flow:
        1. Add a preferred creator
        2. Search for recipes
        3. Verify creator boost in results
        4. Get cached recipe
        """
        user_id = "e2e-test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        # Create a mock preferred creator
        preferred_creator = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="UCpreferred",
            creator_name="Favorite Chef",
        )

        # Mock YouTube results (one from preferred creator, one from random)
        now = datetime.now(UTC)
        mock_youtube_results = [
            YouTubeSearchResult(
                video_id="preferred_video",
                title="Chicken Pasta by Favorite Chef",
                thumbnail_url="https://example.com/thumb1.jpg",
                channel_id="UCpreferred",  # Matches preferred creator
                channel_name="Favorite Chef",
                description="Ingredients: chicken, pasta, tomatoes, garlic, basil",
                published_at=now,
                duration="PT15M",
            ),
            YouTubeSearchResult(
                video_id="random_video",
                title="Chicken Pasta by Random Chef",
                thumbnail_url="https://example.com/thumb2.jpg",
                channel_id="UCreandom",
                channel_name="Random Chef",
                description="Ingredients: chicken, pasta, tomato sauce",
                published_at=now,
                duration="PT10M",
            ),
        ]

        # Mock query generator
        mock_queries = SearchQueries(
            direct_queries=["chicken pasta recipe"],
            dish_suggestions=["chicken pomodoro"],
        )

        # Mock parsed ingredients
        mock_parsed_preferred = ParsedRecipeIngredients(
            ingredients=["chicken", "pasta", "tomatoes", "garlic", "basil"],
            confidence=0.95,
        )

        mock_parsed_random = ParsedRecipeIngredients(
            ingredients=["chicken", "pasta", "tomato sauce"],
            confidence=0.90,
        )

        # Mock match scores
        mock_score_preferred = RecipeMatchScore(
            coverage_score=0.90,
            missing_ingredients=["basil"],
            reasoning="Excellent match with preferred creator",
        )

        mock_score_random = RecipeMatchScore(
            coverage_score=0.75,
            missing_ingredients=["tomato sauce"],
            reasoning="Good match",
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Add preferred creator
            with patch("app.routers.creators.creator_store") as mock_creator_store:
                mock_creator_store.create.return_value = preferred_creator

                response = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "youtube",
                        "url": "https://www.youtube.com/channel/UCpreferred",
                    },
                )

                assert response.status_code == 201
                assert response.json()["creator"]["creator_id"] == "UCpreferred"

            # Step 2: Search for recipes (mock the entire service pipeline)
            with patch("app.routers.recipes.recipe_service.search_recipes", new_callable=AsyncMock) as mock_search:
                # Create expected recipes
                recipe_preferred = Recipe(
                    source="youtube",
                    source_id="preferred_video",
                    url="https://youtube.com/watch?v=preferred_video",
                    thumbnail_url="https://example.com/thumb1.jpg",
                    title="Chicken Pasta by Favorite Chef",
                    creator_name="Favorite Chef",
                    creator_id="UCpreferred",
                    extracted_ingredients=["chicken", "pasta", "tomatoes", "garlic", "basil"],
                    raw_description="...",
                    duration="PT15M",
                    posted_at=now,
                    cache_expires_at=now + timedelta(days=30),
                )

                recipe_random = Recipe(
                    source="youtube",
                    source_id="random_video",
                    url="https://youtube.com/watch?v=random_video",
                    thumbnail_url="https://example.com/thumb2.jpg",
                    title="Chicken Pasta by Random Chef",
                    creator_name="Random Chef",
                    creator_id="UCreandom",
                    extracted_ingredients=["chicken", "pasta", "tomato sauce"],
                    raw_description="...",
                    duration="PT10M",
                    posted_at=now,
                    cache_expires_at=now + timedelta(days=30),
                )

                # Mock service to return both recipes, sorted by score
                from app.services.recipe_collection_service import ScoredRecipe

                mock_search.return_value = [
                    ScoredRecipe(recipe=recipe_preferred, score=mock_score_preferred),
                    ScoredRecipe(recipe=recipe_random, score=mock_score_random),
                ]

                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": user_id,
                        "ingredients": ["chicken", "pasta", "tomatoes"],
                        "max_results": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["recipes"]) == 2

                # Verify preferred creator's recipe is first (higher score)
                assert data["recipes"][0]["recipe"]["creator_id"] == "UCpreferred"
                assert data["recipes"][0]["coverage_score"] == 0.90

            # Step 3: Get cached recipe by ID
            with patch("app.routers.recipes.recipe_cache") as mock_cache:
                mock_cache.get.return_value = recipe_preferred

                response = await client.get(f"/api/internal/recipes/{recipe_preferred.id}")

                assert response.status_code == 200
                cached_data = response.json()
                assert cached_data["id"] == recipe_preferred.id
                assert cached_data["creator_name"] == "Favorite Chef"

    @pytest.mark.asyncio
    async def test_e2e_no_matching_recipes(self):
        """Test E2E flow when no recipes match ingredients."""
        user_id = "test-user-2"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Mock service to return empty results
            with patch("app.routers.recipes.recipe_service.search_recipes", return_value=[]):
                response = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": user_id,
                        "ingredients": ["very_obscure_ingredient"],
                        "max_results": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["recipes"] == []

    @pytest.mark.asyncio
    async def test_e2e_creator_management_flow(self):
        """Test complete creator management flow: add, list, delete."""
        user_id = "creator-test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        creator1 = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="UCcreator1",
            creator_name="Creator 1",
        )

        creator2 = PreferredCreator(
            user_id=user_id,
            source="instagram",
            creator_id="creator2_ig",
            creator_name="Creator 2",
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Add two creators
            with patch("app.routers.creators.creator_store") as mock_store:
                mock_store.create.side_effect = [creator1, creator2]

                # Add first creator
                response1 = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "youtube",
                        "url": "https://www.youtube.com/@creator1",
                    },
                )
                assert response1.status_code == 201

                # Add second creator
                response2 = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "instagram",
                        "url": "https://www.instagram.com/creator2_ig/",
                    },
                )
                assert response2.status_code == 201

            # Step 2: List creators
            with patch("app.routers.creators.creator_store") as mock_store:
                mock_store.list_by_user.return_value = [creator1, creator2]

                response = await client.get("/api/creators", headers=headers)

                assert response.status_code == 200
                creators_list = response.json()
                assert len(creators_list) == 2

            # Step 3: Delete one creator
            with patch("app.routers.creators.creator_store") as mock_store:
                mock_store.get.return_value = creator1
                mock_store.delete.return_value = True

                response = await client.delete(
                    f"/api/creators/{creator1.id}",
                    headers=headers,
                )

                assert response.status_code == 204

            # Step 4: Verify only one creator remains
            with patch("app.routers.creators.creator_store") as mock_store:
                mock_store.list_by_user.return_value = [creator2]

                response = await client.get("/api/creators", headers=headers)

                assert response.status_code == 200
                creators_list = response.json()
                assert len(creators_list) == 1
                assert creators_list[0]["source"] == "instagram"

    @pytest.mark.asyncio
    async def test_e2e_recipe_caching(self):
        """Test that recipes are properly cached and retrieved."""
        now = datetime.now(UTC)

        cached_recipe = Recipe(
            source="youtube",
            source_id="cached_video",
            url="https://youtube.com/watch?v=cached_video",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Cached Recipe",
            creator_name="Chef",
            creator_id="UCchannel",
            extracted_ingredients=["ingredient1", "ingredient2"],
            raw_description="Description",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First request - recipe not in cache, service creates it
            with patch("app.routers.recipes.recipe_service.search_recipes", new_callable=AsyncMock) as mock_search:
                from app.services.recipe_collection_service import ScoredRecipe

                mock_search.return_value = [
                    ScoredRecipe(
                        recipe=cached_recipe,
                        score=RecipeMatchScore(
                            coverage_score=0.8,
                            missing_ingredients=[],
                            reasoning="Match",
                        ),
                    )
                ]

                response1 = await client.post(
                    "/api/internal/recipes/search",
                    json={
                        "user_id": "cache-test-user",
                        "ingredients": ["ingredient1"],
                        "max_results": 5,
                    },
                )

                assert response1.status_code == 200
                data1 = response1.json()
                recipe_id = data1["recipes"][0]["recipe"]["id"]

            # Second request - retrieve from cache
            with patch("app.routers.recipes.recipe_cache") as mock_cache:
                mock_cache.get.return_value = cached_recipe

                response2 = await client.get(f"/api/internal/recipes/{recipe_id}")

                assert response2.status_code == 200
                data2 = response2.json()
                assert data2["id"] == cached_recipe.id
                assert data2["title"] == "Cached Recipe"
