import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC, timedelta

from app.services.recipe_collection_service import RecipeCollectionService, ScoredRecipe
from app.services.query_generator import SearchQueries
from app.services.description_parser import ParsedRecipeIngredients
from app.services.recipe_matcher import RecipeMatchScore
from app.services.youtube_client import YouTubeSearchResult
from app.services.instagram_client import InstagramSearchResult
from app.models.recipe import Recipe, PreferredCreator


@pytest.fixture
def service():
    """Create RecipeCollectionService instance."""
    return RecipeCollectionService()


@pytest.fixture
def mock_query_generator():
    """Mock QueryGenerator."""
    mock = AsyncMock()
    mock.generate.return_value = SearchQueries(
        direct_queries=["chicken pasta recipe", "garlic chicken recipe"],
        dish_suggestions=["chicken pomodoro", "tuscan chicken"],
    )
    return mock


@pytest.fixture
def mock_youtube_results():
    """Mock YouTube search results."""
    now = datetime.now(UTC)
    return [
        YouTubeSearchResult(
            video_id="video1",
            title="Chicken Pasta Recipe",
            thumbnail_url="https://example.com/thumb1.jpg",
            channel_id="UCchannel1",
            channel_name="Chef's Kitchen",
            description="Delicious chicken pasta. Ingredients: chicken, pasta, tomatoes, garlic, basil.",
            published_at=now,
            duration="PT10M",
        ),
        YouTubeSearchResult(
            video_id="video2",
            title="Quick Pasta",
            thumbnail_url="https://example.com/thumb2.jpg",
            channel_id="UCchannel2",
            channel_name="Quick Meals",
            description="Quick pasta recipe. Ingredients: pasta, tomato sauce, cheese.",
            published_at=now,
            duration="PT5M",
        ),
    ]


@pytest.fixture
def mock_instagram_results():
    """Mock Instagram search results."""
    now = datetime.now(UTC)
    return [
        InstagramSearchResult(
            post_id="post1",
            shortcode="ABC123",
            caption="Tasty chicken dish! chicken, rice, vegetables",
            thumbnail_url="https://example.com/ig1.jpg",
            account_username="food_lover",
            account_id="12345",
            posted_at=now,
        ),
    ]


@pytest.mark.asyncio
async def test_search_recipes_success(service, mock_query_generator, mock_youtube_results):
    """Test successful recipe search."""
    # Mock all dependencies
    service.query_generator = mock_query_generator

    with patch.object(service, '_search_youtube', return_value=mock_youtube_results), \
         patch.object(service, '_search_instagram', return_value=[]), \
         patch.object(service, '_convert_to_recipes') as mock_convert, \
         patch.object(service, '_score_recipes') as mock_score:

        # Mock recipe conversion
        now = datetime.now(UTC)
        mock_recipes = [
            Recipe(
                source="youtube",
                source_id="video1",
                url="https://youtube.com/watch?v=video1",
                thumbnail_url="https://example.com/thumb1.jpg",
                title="Chicken Pasta Recipe",
                creator_name="Chef's Kitchen",
                creator_id="UCchannel1",
                extracted_ingredients=["chicken", "pasta", "tomatoes", "garlic", "basil"],
                raw_description="...",
                duration="PT10M",
                posted_at=now,
                cache_expires_at=now + timedelta(days=30),
            )
        ]
        mock_convert.return_value = mock_recipes

        # Mock scoring
        mock_score.return_value = [
            ScoredRecipe(
                recipe=mock_recipes[0],
                score=RecipeMatchScore(
                    coverage_score=0.9,
                    missing_ingredients=["basil"],
                    reasoning="Great match",
                ),
            )
        ]

        results = await service.search_recipes("user123", ["chicken", "pasta", "tomatoes"], max_results=10)

        assert len(results) == 1
        assert results[0].recipe.title == "Chicken Pasta Recipe"
        assert results[0].score.coverage_score == 0.9


@pytest.mark.asyncio
async def test_search_recipes_empty_ingredients(service):
    """Test search with empty ingredients list."""
    service.query_generator = AsyncMock()
    service.query_generator.generate.return_value = SearchQueries(
        direct_queries=[],
        dish_suggestions=[],
    )

    results = await service.search_recipes("user123", [], max_results=10)

    # Should return empty if no queries generated
    assert results == []


@pytest.mark.asyncio
async def test_search_recipes_youtube_fails_instagram_succeeds(
    service, mock_query_generator, mock_instagram_results
):
    """Test graceful degradation when YouTube fails."""
    service.query_generator = mock_query_generator

    with patch.object(service, '_search_youtube', side_effect=Exception("YouTube down")), \
         patch.object(service, '_search_instagram', return_value=mock_instagram_results), \
         patch.object(service, '_convert_to_recipes') as mock_convert, \
         patch.object(service, '_score_recipes') as mock_score:

        now = datetime.now(UTC)
        mock_recipes = [
            Recipe(
                source="instagram",
                source_id="post1",
                url="https://instagram.com/p/ABC123/",
                thumbnail_url="https://example.com/ig1.jpg",
                title="Tasty chicken dish",
                creator_name="food_lover",
                creator_id="12345",
                extracted_ingredients=["chicken", "rice", "vegetables"],
                raw_description="...",
                posted_at=now,
                cache_expires_at=now + timedelta(days=30),
            )
        ]
        mock_convert.return_value = mock_recipes

        mock_score.return_value = [
            ScoredRecipe(
                recipe=mock_recipes[0],
                score=RecipeMatchScore(
                    coverage_score=0.75,
                    missing_ingredients=["rice"],
                    reasoning="Good match",
                ),
            )
        ]

        results = await service.search_recipes("user123", ["chicken", "vegetables"], max_results=10)

        # Should still get results from Instagram
        assert len(results) > 0
        assert results[0].recipe.source == "instagram"


@pytest.mark.asyncio
async def test_search_recipes_both_sources_fail(service, mock_query_generator):
    """Test error when both sources fail."""
    service.query_generator = mock_query_generator

    with patch.object(service, '_search_youtube', side_effect=Exception("YouTube down")), \
         patch.object(service, '_search_instagram', side_effect=Exception("Instagram down")):

        with pytest.raises(Exception) as exc_info:
            await service.search_recipes("user123", ["chicken"], max_results=10)

        assert "No recipes found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_recipes_with_preferred_creators(service, mock_query_generator, mock_youtube_results):
    """Test that preferred creators are passed to search."""
    service.query_generator = mock_query_generator

    # Mock creator store
    with patch("app.services.recipe_collection_service.creator_store") as mock_store:
        mock_store.list_by_user.return_value = [
            PreferredCreator(
                user_id="user123",
                source="youtube",
                creator_id="UCpreferred",
                creator_name="Favorite Chef",
            ),
        ]

        now = datetime.now(UTC)
        mock_recipe = Recipe(
            source="youtube",
            source_id="video1",
            url="https://youtube.com/watch?v=video1",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Recipe",
            creator_name="Chef",
            creator_id="UCchannel",
            extracted_ingredients=["chicken"],
            raw_description="...",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )

        with patch.object(service, '_search_youtube') as mock_yt_search, \
             patch.object(service, '_search_instagram', return_value=[]), \
             patch.object(service, '_convert_to_recipes', return_value=[mock_recipe]), \
             patch.object(service, '_score_recipes') as mock_score:

            mock_yt_search.return_value = mock_youtube_results
            mock_score.return_value = [
                ScoredRecipe(
                    recipe=mock_recipe,
                    score=RecipeMatchScore(coverage_score=0.8, missing_ingredients=[], reasoning="Match"),
                )
            ]

            await service.search_recipes("user123", ["chicken"], max_results=10)

            # Verify preferred channels were passed
            call_args = mock_yt_search.call_args
            youtube_channels = call_args[0][1]
            assert "UCpreferred" in youtube_channels


@pytest.mark.asyncio
async def test_search_youtube_deduplicates_results(service):
    """Test that YouTube search deduplicates by video_id."""
    now = datetime.now(UTC)

    # Create duplicate results
    duplicate_results = [
        YouTubeSearchResult(
            video_id="video1",
            title="Recipe 1",
            thumbnail_url="https://example.com/thumb.jpg",
            channel_id="UCchannel",
            channel_name="Chef",
            description="Test",
            published_at=now,
        ),
        YouTubeSearchResult(
            video_id="video1",  # Duplicate
            title="Recipe 1 Again",
            thumbnail_url="https://example.com/thumb.jpg",
            channel_id="UCchannel",
            channel_name="Chef",
            description="Test",
            published_at=now,
        ),
        YouTubeSearchResult(
            video_id="video2",
            title="Recipe 2",
            thumbnail_url="https://example.com/thumb.jpg",
            channel_id="UCchannel",
            channel_name="Chef",
            description="Test",
            published_at=now,
        ),
    ]

    with patch.object(service.youtube_client, 'search_videos', return_value=duplicate_results):
        results = await service._search_youtube(["test"], [])

        # Should deduplicate
        assert len(results) == 2
        video_ids = [r.video_id for r in results]
        assert "video1" in video_ids
        assert "video2" in video_ids


@pytest.mark.asyncio
async def test_convert_to_recipes_uses_cache(service):
    """Test that recipe conversion checks cache first."""
    now = datetime.now(UTC)

    yt_result = YouTubeSearchResult(
        video_id="cached_video",
        title="Cached Recipe",
        thumbnail_url="https://example.com/thumb.jpg",
        channel_id="UCchannel",
        channel_name="Chef",
        description="Recipe description",
        published_at=now,
    )

    cached_recipe = Recipe(
        source="youtube",
        source_id="cached_video",
        url="https://youtube.com/watch?v=cached_video",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Cached Recipe",
        creator_name="Chef",
        creator_id="UCchannel",
        extracted_ingredients=["chicken", "rice"],
        raw_description="...",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )

    with patch("app.services.recipe_collection_service.recipe_cache") as mock_cache:
        mock_cache.get_by_source.return_value = cached_recipe

        recipes = await service._convert_to_recipes([yt_result], [])

        # Should return cached recipe without parsing
        assert len(recipes) == 1
        assert recipes[0].id == cached_recipe.id
        # Parser should not be called
        assert not hasattr(service.description_parser, 'called')


@pytest.mark.asyncio
async def test_convert_to_recipes_parses_new_recipes(service):
    """Test that new recipes are parsed and cached."""
    now = datetime.now(UTC)

    yt_result = YouTubeSearchResult(
        video_id="new_video",
        title="New Recipe",
        thumbnail_url="https://example.com/thumb.jpg",
        channel_id="UCchannel",
        channel_name="Chef",
        description="Ingredients: chicken, rice, broccoli",
        published_at=now,
        duration="PT10M",
    )

    mock_parsed = ParsedRecipeIngredients(
        ingredients=["chicken", "rice", "broccoli"],
        confidence=0.9,
    )

    with patch("app.services.recipe_collection_service.recipe_cache") as mock_cache, \
         patch.object(service.description_parser, 'parse', return_value=mock_parsed):

        mock_cache.get_by_source.return_value = None  # Not in cache

        recipes = await service._convert_to_recipes([yt_result], [])

        # Should parse and cache
        assert len(recipes) == 1
        assert recipes[0].extracted_ingredients == ["chicken", "rice", "broccoli"]
        # Verify it was cached
        assert mock_cache.put.called


@pytest.mark.asyncio
async def test_convert_to_recipes_skips_low_confidence(service):
    """Test that low-confidence recipes are skipped."""
    now = datetime.now(UTC)

    yt_result = YouTubeSearchResult(
        video_id="vlog_video",
        title="My Day Vlog",
        thumbnail_url="https://example.com/thumb.jpg",
        channel_id="UCchannel",
        channel_name="Vlogger",
        description="Just my daily vlog, not a recipe",
        published_at=now,
    )

    mock_parsed = ParsedRecipeIngredients(
        ingredients=[],
        confidence=0.2,  # Low confidence - not a recipe
    )

    with patch("app.services.recipe_collection_service.recipe_cache") as mock_cache, \
         patch.object(service.description_parser, 'parse', return_value=mock_parsed):

        mock_cache.get_by_source.return_value = None

        recipes = await service._convert_to_recipes([yt_result], [])

        # Should be filtered out
        assert len(recipes) == 0


@pytest.mark.asyncio
async def test_score_recipes_filters_low_scores(service):
    """Test that very low-scoring recipes are filtered out."""
    now = datetime.now(UTC)

    recipes = [
        Recipe(
            source="youtube",
            source_id="video1",
            url="https://youtube.com/watch?v=video1",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Recipe",
            creator_name="Chef",
            creator_id="UCchannel",
            extracted_ingredients=["ingredient1", "ingredient2"],
            raw_description="...",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )
    ]

    mock_scores = {
        recipes[0].id: RecipeMatchScore(
            coverage_score=0.05,  # Very low
            missing_ingredients=["many", "ingredients"],
            reasoning="Poor match",
        )
    }

    with patch.object(service.recipe_matcher, 'score_batch', return_value=mock_scores):
        scored = await service._score_recipes(recipes, ["user_ingredient"])

        # Should filter out score < 0.1
        assert len(scored) == 0


@pytest.mark.asyncio
async def test_search_recipes_limits_results(service, mock_query_generator, mock_youtube_results):
    """Test that results are limited to max_results."""
    service.query_generator = mock_query_generator

    # Create many scored recipes
    now = datetime.now(UTC)
    many_recipes = []
    for i in range(20):
        recipe = Recipe(
            source="youtube",
            source_id=f"video{i}",
            url=f"https://youtube.com/watch?v=video{i}",
            thumbnail_url="https://example.com/thumb.jpg",
            title=f"Recipe {i}",
            creator_name="Chef",
            creator_id="UCchannel",
            extracted_ingredients=["chicken", "rice"],
            raw_description="...",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )
        many_recipes.append(recipe)

    scored_recipes = [
        ScoredRecipe(
            recipe=r,
            score=RecipeMatchScore(
                coverage_score=0.8 - (i * 0.01),  # Descending scores
                missing_ingredients=[],
                reasoning="Match",
            ),
        )
        for i, r in enumerate(many_recipes)
    ]

    with patch.object(service, '_search_youtube', return_value=mock_youtube_results), \
         patch.object(service, '_search_instagram', return_value=[]), \
         patch.object(service, '_convert_to_recipes', return_value=many_recipes), \
         patch.object(service, '_score_recipes', return_value=scored_recipes):

        results = await service.search_recipes("user123", ["chicken", "rice"], max_results=5)

        # Should limit to 5
        assert len(results) == 5
        # Should be sorted by score (best first)
        assert results[0].score.coverage_score > results[4].score.coverage_score


@pytest.mark.asyncio
async def test_search_all_platforms_youtube_only(service, mock_youtube_results, mock_instagram_results):
    """Test _search_all_platforms with only YouTube enabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = False

        service._search_youtube = AsyncMock(return_value=mock_youtube_results)
        service._search_instagram = AsyncMock(return_value=mock_instagram_results)

        queries = ["chicken recipe"]
        yt_results, ig_results = await service._search_all_platforms(queries, [], [])

        # YouTube should be called
        service._search_youtube.assert_called_once_with(queries, [])
        # Instagram should NOT be called
        service._search_instagram.assert_not_called()

        assert yt_results == mock_youtube_results
        assert ig_results == []


@pytest.mark.asyncio
async def test_search_all_platforms_instagram_only(service, mock_youtube_results, mock_instagram_results):
    """Test _search_all_platforms with only Instagram enabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = False
        mock_settings.enable_instagram_source = True

        service._search_youtube = AsyncMock(return_value=mock_youtube_results)
        service._search_instagram = AsyncMock(return_value=mock_instagram_results)

        queries = ["chicken recipe"]
        yt_results, ig_results = await service._search_all_platforms(queries, [], [])

        # YouTube should NOT be called
        service._search_youtube.assert_not_called()
        # Instagram should be called
        service._search_instagram.assert_called_once_with(queries, [])

        assert yt_results == []
        assert ig_results == mock_instagram_results


@pytest.mark.asyncio
async def test_search_all_platforms_both_enabled(service, mock_youtube_results, mock_instagram_results):
    """Test _search_all_platforms with both sources enabled (existing behavior)."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = True

        service._search_youtube = AsyncMock(return_value=mock_youtube_results)
        service._search_instagram = AsyncMock(return_value=mock_instagram_results)

        queries = ["chicken recipe"]
        yt_results, ig_results = await service._search_all_platforms(queries, [], [])

        # Both should be called
        service._search_youtube.assert_called_once_with(queries, [])
        service._search_instagram.assert_called_once_with(queries, [])

        assert yt_results == mock_youtube_results
        assert ig_results == mock_instagram_results


@pytest.mark.asyncio
async def test_search_all_platforms_handles_exceptions_with_disabled_source(service, mock_youtube_results):
    """Test exception handling when one source is disabled and other fails."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = False

        service._search_youtube = AsyncMock(side_effect=Exception("API error"))
        service._search_instagram = AsyncMock()

        queries = ["chicken recipe"]
        yt_results, ig_results = await service._search_all_platforms(queries, [], [])

        # Should handle exception gracefully
        assert yt_results == []
        assert ig_results == []
        service._search_instagram.assert_not_called()
