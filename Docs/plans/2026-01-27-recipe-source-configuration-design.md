# Recipe Source Configuration via Environment Variables

**Date:** 2026-01-27
**Status:** Approved
**Type:** Feature Enhancement

## Overview

Add environment variable configuration to enable/disable YouTube and Instagram recipe sources independently. This allows operators to disable sources without code changes, useful for:
- Testing with limited sources
- Handling API outages or rate limits
- Reducing costs by disabling expensive APIs
- Gradual rollout of new sources

## Configuration Design

### Environment Variables

Add to `.env.example` and `.env`:

```bash
# Recipe source configuration
ENABLE_YOUTUBE_SOURCE=true
ENABLE_INSTAGRAM_SOURCE=true
```

**Format:** Individual boolean flags per source
**Default:** Both enabled (backwards compatible)
**Supported values:** true/false, 1/0, yes/no (Pydantic automatic conversion)

### Settings Class

Update `backend/app/config.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str = ""
    youtube_api_key: str = ""
    instagram_rapidapi_key: str = ""

    # Recipe source toggles
    enable_youtube_source: bool = True
    enable_instagram_source: bool = True

    # JWT Settings (existing)
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

# Call validation when settings are loaded
settings = Settings()
settings.validate_sources()
```

## Service Layer Changes

### Update `_search_all_platforms()` Method

Location: `backend/app/services/recipe_collection_service.py`

**Current behavior:** Always searches both platforms in parallel using `asyncio.gather()`

**New behavior:** Only search enabled sources, maintaining parallelism

```python
import logging

logger = logging.getLogger(__name__)

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

### Update Progress Messages

Around line 103-111 in `recipe_collection_service.py`:

```python
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

### Update Error Messages

Around line 117-118:

```python
if not youtube_results and not instagram_results:
    enabled = settings.enabled_sources
    raise Exception(
        f"No recipes found from enabled sources: {', '.join(enabled)}"
    )
```

## Error Handling & Validation

### Startup Validation

- **When:** Application startup (when `settings` object is created)
- **Check:** At least one source is enabled
- **Error:** Clear `ValueError` with instructions on which env vars to set
- **Result:** Application fails to start if misconfigured (fail-fast principle)

### Runtime Error Handling

- **Source disabled:** Skip entirely, no task created
- **Source fails:** Log warning, return empty results (existing behavior preserved)
- **No results from any enabled source:** Raise exception with list of enabled sources

### Logging Strategy

- **INFO level:** Log when a source is intentionally disabled (at method start)
- **WARNING level:** Log when an enabled source fails (during gather exception handling)
- **ERROR level:** (existing) When no results from any source

## Testing Strategy

### Configuration Tests

Test `Settings` class:
- Default values (both enabled)
- Individual source disabled
- Both sources disabled (should raise ValueError)
- `enabled_sources` property returns correct list

### Service Tests

Test `_search_all_platforms()`:
- Both sources enabled (existing behavior)
- Only YouTube enabled
- Only Instagram enabled
- Source enabled but API fails (should return empty, not crash)
- Progress messages reflect enabled sources

### Integration Tests

- End-to-end recipe search with different source configurations
- Error messages show correct enabled sources

## Migration Path

### Backwards Compatibility

**100% backwards compatible:**
- Default values enable both sources
- Existing deployments without new env vars work unchanged
- No database migrations needed
- No API changes

### Deployment

1. Update `.env.example` with new variables
2. Deploy code changes
3. Optionally add env vars to production `.env` (not required)
4. Restart application

### Rollback

Simply remove the new env vars or set both to `true`. No data migrations to revert.

## Future Enhancements

### Potential additions (out of scope for this change):

1. **Per-user source preferences** - Allow users to disable sources in their profile
2. **Dynamic source registration** - Plugin system for adding new sources
3. **Source health checks** - Automatically disable failing sources temporarily
4. **Rate limit configuration** - Per-source rate limiting via env vars
5. **Source prioritization** - Configure which source to search first

## Benefits

- **Operational flexibility:** Disable sources without code deployment
- **Cost control:** Turn off expensive APIs when needed
- **Testing:** Test with limited sources during development
- **Graceful degradation:** Handle API outages by disabling temporarily
- **Clear visibility:** Logs and messages show which sources are active
- **Type safety:** Pydantic validates boolean values automatically
- **Fail-fast:** Invalid configuration caught at startup

## Implementation Checklist

- [ ] Update `.env.example` with new variables
- [ ] Add fields to `Settings` class in `config.py`
- [ ] Add `enabled_sources` property
- [ ] Add `validate_sources()` method and call it
- [ ] Update `_search_all_platforms()` to conditionally search
- [ ] Add logging for disabled sources
- [ ] Update progress messages
- [ ] Update error messages
- [ ] Add unit tests for `Settings`
- [ ] Add unit tests for `_search_all_platforms()`
- [ ] Add integration tests
- [ ] Update documentation
