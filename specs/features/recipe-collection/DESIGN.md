---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/ARCHITECTURE.md#backend-patterns
  - ../../../specs/DOMAIN.md#recipe
  - ../../../specs/DOMAIN.md#preferredcreator
status: implemented
---

# Design: Recipe Collection

Technical implementation of the recipe collection feature.

## Data Models

### Recipe

```python
class Recipe(BaseModel):
    id: str                         # Internal UUID
    source: Literal["youtube", "instagram"]
    source_id: str                  # Platform video/post ID
    url: str                        # Direct link
    thumbnail_url: str
    title: str
    creator_name: str
    creator_id: str
    extracted_ingredients: list[str]  # Parsed from description
    raw_description: str
    duration: Optional[str]         # YouTube only
    posted_at: datetime
    cached_at: datetime
    cache_expires_at: datetime      # 24-hour TTL
```

### ScoredRecipe (runtime)

```python
class ScoredRecipe(BaseModel):
    recipe: Recipe
    coverage_score: float           # 0-1, % ingredients matched
    matched_ingredients: list[str]
    missing_ingredients: list[str]
```

## Search Pipeline

```
User Ingredients
       ↓
┌──────────────────┐
│  Query Generator │ → LLM generates search terms
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Platform Search  │ → YouTube + Instagram in parallel
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Description Parse│ → LLM extracts ingredients
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Recipe Matcher  │ → LLM scores against user ingredients
└────────┬─────────┘
         ↓
Top 10-15 ScoredRecipes → Meal Plan Generator
```

## Backend Services

```
RecipeCollectionService
├── QueryGenerator          # LLM search query generation
├── YouTubeClient           # YouTube Data API v3
├── InstagramClient         # RapidAPI wrapper
├── DescriptionParser       # LLM ingredient extraction
├── RecipeMatcher           # LLM scoring
└── RecipeCache             # In-memory with TTL
```

### QueryGenerator

```python
class QueryGenerator:
    async def generate(self, ingredients: list[str]) -> list[str]:
        # Returns both direct queries and AI-suggested dishes
        # "chicken tomato pasta recipe"
        # "chicken pomodoro"
        # "tuscan chicken"
```

### RecipeMatcher

```python
class RecipeMatcher:
    async def score(
        self,
        recipe: Recipe,
        user_ingredients: list[str]
    ) -> ScoredRecipe:
        # LLM compares ingredients, handles substitutions
        # Returns coverage_score + matched/missing lists
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/recipes/search` | POST | Search recipes (internal) |
| `/api/recipes/session/{id}` | GET | Get cached recipes |

### Search Request/Response

```python
# Request
class SearchRequest(BaseModel):
    ingredients: list[str]
    user_id: str

# Response
class SearchResponse(BaseModel):
    recipes: list[ScoredRecipe]
```

## External APIs

### YouTube Data API v3

```python
class YouTubeClient:
    async def search(
        self,
        queries: list[str],
        channel_ids: list[str]  # Preferred creators
    ) -> list[Recipe]:
        # Uses search.list endpoint
        # Fetches video details for duration, description
```

### Instagram (RapidAPI)

```python
class InstagramClient:
    async def search(
        self,
        queries: list[str],
        accounts: list[str]  # Preferred creators
    ) -> list[Recipe]:
        # Third-party service for public posts
```

## Configuration

```bash
# Environment variables
ENABLE_YOUTUBE_SOURCE=true
ENABLE_INSTAGRAM_SOURCE=true
YOUTUBE_API_KEY=...
INSTAGRAM_RAPIDAPI_KEY=...
```

## Caching Strategy

- **TTL**: 24 hours per recipe
- **Key**: `{source}:{source_id}`
- **Storage**: In-memory dict (future: Redis)
- **Behavior**: Check cache before API call, skip re-parsing cached

## Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| YouTube API down | HTTP error | Retry once, use Instagram only |
| Instagram down | HTTP error | Retry once, use YouTube only |
| Both down | Both fail | Block with user message |
| Rate limit (429) | Response code | Use cached results only |
| LLM parse failure | OpenAI error | Retry 2x, exclude unparsed |

## Testing

### Unit Tests
- QueryGenerator: ingredients → relevant queries
- DescriptionParser: various formats → ingredients
- RecipeMatcher: scoring logic, coverage calculation

### Integration Tests
- Full pipeline with mocked APIs
- Cache hit/miss behavior
- Creator priority ranking

## Related Documents

- Original design: [Docs/plans/2026-01-26-recipe-collection-design.md](../../../Docs/plans/2026-01-26-recipe-collection-design.md)
- Source config: [Docs/plans/2026-01-27-recipe-source-configuration-design.md](../../../Docs/plans/2026-01-27-recipe-source-configuration-design.md)
