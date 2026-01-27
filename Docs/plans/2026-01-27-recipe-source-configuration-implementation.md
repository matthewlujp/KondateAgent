# Recipe Source Configuration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add environment variable configuration to independently enable/disable YouTube and Instagram recipe sources.

**Architecture:** Add boolean flags to Settings class with validation, update RecipeCollectionService to conditionally search enabled sources while maintaining parallel execution, update progress/error messages to reflect active sources.

**Tech Stack:** Python, Pydantic Settings, pytest, asyncio

---

## Task 1: Configuration Layer - Add Settings Fields

**Files:**
- Modify: `backend/app/config.py:1-17`
- Modify: `backend/.env.example:1-4`

**Step 1: Write failing test for Settings**

Create: `backend/tests/test_config.py`

```python
import pytest
from unittest.mock import patch
from app.config import Settings


def test_default_sources_enabled():
    """Test that both sources are enabled by default."""
    settings = Settings()
    assert settings.enable_youtube_source is True
    assert settings.enable_instagram_source is True


def test_enabled_sources_property_both():
    """Test enabled_sources property returns both sources."""
    settings = Settings()
    assert settings.enabled_sources == ["youtube", "instagram"]


def test_enabled_sources_property_youtube_only():
    """Test enabled_sources property with only YouTube enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "true", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        assert settings.enabled_sources == ["youtube"]


def test_enabled_sources_property_instagram_only():
    """Test enabled_sources property with only Instagram enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "false", "ENABLE_INSTAGRAM_SOURCE": "true"}):
        settings = Settings()
        assert settings.enabled_sources == ["instagram"]


def test_validate_sources_fails_when_both_disabled():
    """Test that validation fails when both sources are disabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "false", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_sources()
        assert "at least one recipe source must be enabled" in str(exc_info.value).lower()


def test_validate_sources_passes_with_one_enabled():
    """Test that validation passes with at least one source enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "true", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        settings.validate_sources()  # Should not raise
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_config.py -v`

Expected: Multiple FAILs - AttributeError: 'Settings' object has no attribute 'enable_youtube_source'

**Step 3: Update .env.example**

Modify: `backend/.env.example`

Add after line 3:
```bash
# Recipe source configuration
ENABLE_YOUTUBE_SOURCE=true
ENABLE_INSTAGRAM_SOURCE=true
```

**Step 4: Add fields and methods to Settings class**

Modify: `backend/app/config.py`

Replace the Settings class (lines 4-17):
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str = ""
    youtube_api_key: str = ""
    instagram_rapidapi_key: str = ""

    # Recipe source toggles
    enable_youtube_source: bool = True
    enable_instagram_source: bool = True

    # JWT Settings
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @property
    def enabled_sources(self) -> list[str]:
        """Get list of enabled source names."""
        sources = []
        if self.enable_youtube_source:
            sources.append("youtube")
        if self.enable_instagram_source:
            sources.append("instagram")
        return sources

    def validate_sources(self) -> None:
        """Ensure at least one source is enabled."""
        if not self.enable_youtube_source and not self.enable_instagram_source:
            raise ValueError(
                "At least one recipe source must be enabled. "
                "Set ENABLE_YOUTUBE_SOURCE=true or ENABLE_INSTAGRAM_SOURCE=true"
            )


settings = Settings()
settings.validate_sources()
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_config.py -v`

Expected: 6 passed

**Step 6: Commit**

```bash
git add backend/app/config.py backend/.env.example backend/tests/test_config.py
git commit -m "feat: add source toggle configuration to Settings

- Add enable_youtube_source and enable_instagram_source boolean flags
- Add enabled_sources property to get active sources
- Add validate_sources() to ensure at least one source enabled
- Call validation on settings initialization
- Update .env.example with new variables
- Add comprehensive tests for Settings configuration

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Service Layer - Update _search_all_platforms Method

**Files:**
- Modify: `backend/app/services/recipe_collection_service.py:164-190`

**Step 1: Write failing test for conditional source searching**

Add to: `backend/tests/test_recipe_collection_service.py`

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_search_all_platforms_youtube_only -v`

Expected: FAIL - Instagram was still called (current behavior always searches both)

**Step 3: Add logging import at top of file**

Modify: `backend/app/services/recipe_collection_service.py`

Add after existing imports (around line 1-10):
```python
import logging

logger = logging.getLogger(__name__)
```

**Step 4: Replace _search_all_platforms method**

Modify: `backend/app/services/recipe_collection_service.py:164-190`

Replace the entire `_search_all_platforms` method:
```python
    async def _search_all_platforms(
        self,
        queries: list[str],
        youtube_channels: list[str],
        instagram_accounts: list[str],
    ) -> tuple[list, list]:
        """Search enabled platforms in parallel."""

        # Log which sources are enabled/disabled
        if not settings.enable_youtube_source:
            logger.info("YouTube source is disabled")
        if not settings.enable_instagram_source:
            logger.info("Instagram source is disabled")

        # Build task list for enabled sources
        tasks = []
        task_sources = []  # Track which source each task belongs to

        if settings.enable_youtube_source:
            tasks.append(self._search_youtube(queries, youtube_channels))
            task_sources.append("youtube")

        if settings.enable_instagram_source:
            tasks.append(self._search_instagram(queries, instagram_accounts))
            task_sources.append("instagram")

        # Gather all enabled tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to youtube/instagram
        youtube_results = []
        instagram_results = []

        for i, source in enumerate(task_sources):
            result = results[i]
            # Handle exceptions
            if isinstance(result, Exception):
                logger.warning(f"{source.capitalize()} search failed: {result}")
                result = []

            if source == "youtube":
                youtube_results = result
            elif source == "instagram":
                instagram_results = result

        return youtube_results, instagram_results
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_search_all_platforms_youtube_only backend/tests/test_recipe_collection_service.py::test_search_all_platforms_instagram_only backend/tests/test_recipe_collection_service.py::test_search_all_platforms_both_enabled backend/tests/test_recipe_collection_service.py::test_search_all_platforms_handles_exceptions_with_disabled_source -v`

Expected: 4 passed

**Step 6: Commit**

```bash
git add backend/app/services/recipe_collection_service.py backend/tests/test_recipe_collection_service.py
git commit -m "feat: update _search_all_platforms to respect source configuration

- Only search enabled sources based on settings
- Maintain parallel execution with asyncio.gather
- Add logging for disabled sources
- Handle exceptions per source
- Add comprehensive tests for all configurations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Progress Messages - Update to Reflect Enabled Sources

**Files:**
- Modify: `backend/app/services/recipe_collection_service.py:102-115`

**Step 1: Write test for progress message content**

Add to: `backend/tests/test_recipe_collection_service.py`

```python
@pytest.mark.asyncio
async def test_collect_progress_message_reflects_enabled_sources_youtube_only(
    service, mock_query_generator, mock_youtube_results
):
    """Test progress message shows only YouTube when Instagram is disabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = False
        mock_settings.enabled_sources = ["youtube"]

        service.query_generator = mock_query_generator
        service._search_all_platforms = AsyncMock(return_value=(mock_youtube_results, []))
        service._parse_recipe_descriptions = AsyncMock(return_value=[])
        service._score_and_rank_recipes = AsyncMock(return_value=[])

        progress_events = []

        async def capture_progress(event):
            progress_events.append(event)

        try:
            await service.collect_recipes(
                ["chicken", "pasta"],
                max_results=5,
                user_id="test_user",
                on_progress=capture_progress,
            )
        except Exception:
            pass  # Expected to fail due to empty results

        # Find the searching_platforms progress event
        search_event = next(
            (e for e in progress_events if e.phase == "searching_platforms"), None
        )
        assert search_event is not None
        assert "youtube" in search_event.message.lower()
        assert "instagram" not in search_event.message.lower()


@pytest.mark.asyncio
async def test_collect_progress_message_reflects_enabled_sources_both(
    service, mock_query_generator, mock_youtube_results, mock_instagram_results
):
    """Test progress message shows both sources when both enabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = True
        mock_settings.enabled_sources = ["youtube", "instagram"]

        service.query_generator = mock_query_generator
        service._search_all_platforms = AsyncMock(
            return_value=(mock_youtube_results, mock_instagram_results)
        )
        service._parse_recipe_descriptions = AsyncMock(return_value=[])
        service._score_and_rank_recipes = AsyncMock(return_value=[])

        progress_events = []

        async def capture_progress(event):
            progress_events.append(event)

        try:
            await service.collect_recipes(
                ["chicken", "pasta"],
                max_results=5,
                user_id="test_user",
                on_progress=capture_progress,
            )
        except Exception:
            pass  # Expected to fail due to empty results

        # Find the searching_platforms progress event
        search_event = next(
            (e for e in progress_events if e.phase == "searching_platforms"), None
        )
        assert search_event is not None
        assert "youtube" in search_event.message.lower()
        assert "instagram" in search_event.message.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_collect_progress_message_reflects_enabled_sources_youtube_only -v`

Expected: FAIL - Message still contains "YouTube and Instagram"

**Step 3: Update progress message in collect_recipes method**

Modify: `backend/app/services/recipe_collection_service.py` around lines 103-111

Replace the progress event creation:
```python
        # Step 3: Search both platforms in parallel
        if on_progress:
            enabled_sources = settings.enabled_sources
            source_list = " and ".join(enabled_sources)
            await on_progress(
                ProgressEvent(
                    step=2,
                    total_steps=5,
                    phase="searching_platforms",
                    message=f"Searching {source_list} for recipes...",
                )
            )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_collect_progress_message_reflects_enabled_sources_youtube_only backend/tests/test_recipe_collection_service.py::test_collect_progress_message_reflects_enabled_sources_both -v`

Expected: 2 passed

**Step 5: Commit**

```bash
git add backend/app/services/recipe_collection_service.py backend/tests/test_recipe_collection_service.py
git commit -m "feat: update progress messages to reflect enabled sources

- Progress message now shows only enabled sources
- Use settings.enabled_sources to build dynamic message
- Add tests for different source configurations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Error Messages - Update to Show Enabled Sources

**Files:**
- Modify: `backend/app/services/recipe_collection_service.py:117-118`

**Step 1: Write test for error message content**

Add to: `backend/tests/test_recipe_collection_service.py`

```python
@pytest.mark.asyncio
async def test_collect_error_message_shows_enabled_sources(
    service, mock_query_generator
):
    """Test error message shows which sources were enabled when no results found."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = False
        mock_settings.enabled_sources = ["youtube"]

        service.query_generator = mock_query_generator
        service._search_all_platforms = AsyncMock(return_value=([], []))

        with pytest.raises(Exception) as exc_info:
            await service.collect_recipes(
                ["chicken", "pasta"],
                max_results=5,
                user_id="test_user",
            )

        error_message = str(exc_info.value)
        assert "enabled sources" in error_message.lower()
        assert "youtube" in error_message.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_collect_error_message_shows_enabled_sources -v`

Expected: FAIL - Error message doesn't mention enabled sources

**Step 3: Update error message in collect_recipes method**

Modify: `backend/app/services/recipe_collection_service.py` around lines 117-118

Replace:
```python
        if not youtube_results and not instagram_results:
            enabled = settings.enabled_sources
            raise Exception(
                f"No recipes found from enabled sources: {', '.join(enabled)}"
            )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_recipe_collection_service.py::test_collect_error_message_shows_enabled_sources -v`

Expected: 1 passed

**Step 5: Commit**

```bash
git add backend/app/services/recipe_collection_service.py backend/tests/test_recipe_collection_service.py
git commit -m "feat: update error messages to show enabled sources

- Error message now lists which sources were enabled
- Helps debugging when no recipes found
- Add test for error message content

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Integration Test - Full Workflow with Source Configuration

**Files:**
- Modify: `backend/tests/test_recipe_collection_integration.py`

**Step 1: Write integration test for source configuration**

Add to: `backend/tests/test_recipe_collection_integration.py`

```python
@pytest.mark.asyncio
async def test_recipe_collection_with_youtube_only():
    """Integration test: collect recipes with only YouTube enabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = True
        mock_settings.enable_instagram_source = False
        mock_settings.enabled_sources = ["youtube"]

        service = RecipeCollectionService()

        # Mock the YouTube client to return results
        mock_youtube_result = YouTubeSearchResult(
            video_id="test_video",
            title="Test Recipe",
            thumbnail_url="https://example.com/thumb.jpg",
            channel_id="UCtest",
            channel_name="Test Channel",
            description="Recipe with chicken and pasta",
            published_at=datetime.now(UTC),
            duration="PT10M",
        )

        service.youtube_client.search_videos = AsyncMock(return_value=[mock_youtube_result])

        # Mock Instagram client to ensure it's not called
        service.instagram_client.search_posts = AsyncMock()

        # Mock description parser
        service.description_parser.parse = AsyncMock(
            return_value=ParsedRecipeIngredients(
                ingredients=["chicken", "pasta"],
                confidence_score=0.9,
            )
        )

        results = await service.collect_recipes(
            ["chicken", "pasta"],
            max_results=5,
            user_id="test_user",
        )

        # Verify results contain only YouTube recipes
        assert len(results) > 0
        for recipe in results:
            assert recipe.source == "youtube"

        # Verify Instagram client was not called
        service.instagram_client.search_posts.assert_not_called()


@pytest.mark.asyncio
async def test_recipe_collection_with_instagram_only():
    """Integration test: collect recipes with only Instagram enabled."""
    with patch("app.services.recipe_collection_service.settings") as mock_settings:
        mock_settings.enable_youtube_source = False
        mock_settings.enable_instagram_source = True
        mock_settings.enabled_sources = ["instagram"]

        service = RecipeCollectionService()

        # Mock the Instagram client to return results
        mock_instagram_result = InstagramSearchResult(
            post_id="test_post",
            caption="Test Recipe with chicken and pasta",
            thumbnail_url="https://example.com/thumb.jpg",
            post_url="https://instagram.com/p/test",
            username="test_user",
            timestamp=datetime.now(UTC),
        )

        service.instagram_client.search_posts = AsyncMock(return_value=[mock_instagram_result])

        # Mock YouTube client to ensure it's not called
        service.youtube_client.search_videos = AsyncMock()

        # Mock description parser
        service.description_parser.parse = AsyncMock(
            return_value=ParsedRecipeIngredients(
                ingredients=["chicken", "pasta"],
                confidence_score=0.9,
            )
        )

        results = await service.collect_recipes(
            ["chicken", "pasta"],
            max_results=5,
            user_id="test_user",
        )

        # Verify results contain only Instagram recipes
        assert len(results) > 0
        for recipe in results:
            assert recipe.source == "instagram"

        # Verify YouTube client was not called
        service.youtube_client.search_videos.assert_not_called()
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_recipe_collection_integration.py::test_recipe_collection_with_youtube_only backend/tests/test_recipe_collection_integration.py::test_recipe_collection_with_instagram_only -v`

Expected: 2 passed

**Step 3: Commit**

```bash
git add backend/tests/test_recipe_collection_integration.py
git commit -m "test: add integration tests for source configuration

- Test full workflow with YouTube only
- Test full workflow with Instagram only
- Verify disabled sources are not called
- Verify results contain only enabled source recipes

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Verify Full Test Suite

**Step 1: Run all tests**

Run: `uv run pytest backend/tests/ -v`

Expected: All tests pass

**Step 2: Check coverage for new code**

Run: `uv run pytest backend/tests/ --cov=app.config --cov=app.services.recipe_collection_service --cov-report=term-missing`

Expected: High coverage (>90%) for modified code

**Step 3: If any tests fail, fix them**

Investigate failures and fix. Common issues:
- Import errors (check imports at top of files)
- Mock patches not matching actual settings usage
- Async/await issues in tests

---

## Task 7: Manual Verification

**Step 1: Test with YouTube only**

Create temporary `.env` file:
```bash
cp backend/.env backend/.env.backup
echo "ENABLE_YOUTUBE_SOURCE=true" >> backend/.env
echo "ENABLE_INSTAGRAM_SOURCE=false" >> backend/.env
```

Run backend and verify logs show "Instagram source is disabled"

**Step 2: Test with Instagram only**

Update `.env`:
```bash
# In backend/.env
ENABLE_YOUTUBE_SOURCE=false
ENABLE_INSTAGRAM_SOURCE=true
```

Run backend and verify logs show "YouTube source is disabled"

**Step 3: Test with both disabled (should fail)**

Update `.env`:
```bash
# In backend/.env
ENABLE_YOUTUBE_SOURCE=false
ENABLE_INSTAGRAM_SOURCE=false
```

Run backend and verify it fails with clear error message about needing at least one source

**Step 4: Restore original .env**

```bash
mv backend/.env.backup backend/.env
```

---

## Task 8: Final Commit and Cleanup

**Step 1: Run final test suite**

Run: `uv run pytest backend/tests/ -v`

Expected: All tests pass

**Step 2: Check git status**

Run: `git status`

Expected: All changes committed, working tree clean

**Step 3: If uncommitted changes exist, review and commit**

Review changes:
```bash
git diff
```

If appropriate, commit:
```bash
git add <files>
git commit -m "chore: final cleanup for source configuration feature

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Implementation Complete

**Summary of changes:**
- Added `enable_youtube_source` and `enable_instagram_source` boolean configuration
- Added `enabled_sources` property and `validate_sources()` method to Settings
- Updated `_search_all_platforms()` to conditionally search enabled sources
- Updated progress messages to reflect active sources
- Updated error messages to show enabled sources
- Added comprehensive unit and integration tests
- Updated `.env.example` with new configuration options

**Verification:**
- All tests pass
- Manual testing confirms sources can be independently disabled
- Application fails fast when both sources disabled
- Progress and error messages accurately reflect configuration

**Next steps:**
- Update production `.env` if needed
- Monitor logs after deployment
- Consider adding source health checks (future enhancement)
