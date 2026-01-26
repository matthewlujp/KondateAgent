# Recipe Collection Feature Design

**Date**: 2026-01-26
**Status**: Approved
**Author**: Collaborative design session

## Overview

Find relevant recipes from YouTube and Instagram based on user's available ingredients, feeding directly into the meal plan generator. Recipe search is invisible infrastructure - users only see the final meal plan.

## User Flow

1. User completes ingredient collection, taps "Plan my meals!"
2. System generates search queries (ingredient-based + AI-suggested dishes)
3. Searches YouTube API and Instagram (via third-party service) - behind the scenes
4. Parses descriptions with LLM to extract ingredient lists
5. Scores recipes against user's ingredients using LLM
6. Top candidates (10-15) passed directly to Meal Plan Generator
7. Meal Plan Generator selects optimal recipes for the week
8. User only sees the final proposed meal plan - can approve or swap dishes

## Creator Registration

Users can register preferred creators who get priority in recipe search:

- **Onboarding**: Light prompt "Add your favorite recipe creators?"
- **Ongoing**: "Follow this creator" button on meal plan results
- **Settings**: Paste YouTube channel URLs or Instagram handles anytime
- Preferred creators get ranking priority in recipe pool

## Data Model

### Recipe

```typescript
interface Recipe {
  id: string;
  source: "youtube" | "instagram";
  source_id: string;          // YouTube video ID or Instagram post ID
  url: string;                // Direct link to content
  thumbnail_url: string;
  title: string;
  creator_name: string;
  creator_id: string;         // Channel ID or Instagram handle
  extracted_ingredients: string[];  // Parsed from description
  raw_description: string;    // Original description for debugging
  duration?: string;          // Video length (YouTube only)
  posted_at: timestamp;
  cached_at: timestamp;
  cache_expires_at: timestamp; // TTL for refresh
}
```

### Preferred Creator

```typescript
interface PreferredCreator {
  id: string;
  user_id: string;
  source: "youtube" | "instagram";
  creator_id: string;
  creator_name: string;
  added_at: timestamp;
}
```

## API Integrations

- **YouTube**: Official Data API v3 (search endpoint + video details)
- **Instagram**: Third-party service (e.g., RapidAPI) for public post search

## Caching Strategy

- Persistent cache with 30-day TTL
- Check cache before API calls
- Re-parse only if cache expired or not found
- Batch API calls where possible to reduce quota usage

## Search & Parsing Pipeline

### Step 1: Query Generation

```
User ingredients: ["chicken breast", "tomatoes", "garlic", "pasta"]
                    ↓
              LLM generates queries
                    ↓
Direct queries:    "chicken tomato pasta recipe"
                   "garlic chicken recipe"
Suggested dishes:  "chicken pomodoro"
                   "garlic butter chicken pasta"
                   "tuscan chicken"
```

### Step 2: Parallel API Search

- Fire queries to YouTube and Instagram simultaneously
- Apply creator boost: prioritize results from user's registered creators
- Collect up to 30-40 raw results across both platforms

### Step 3: Description Parsing (LLM)

```
Input:  Video title + description text
Output: {
  ingredients: ["chicken breast", "tomatoes", "garlic", "olive oil", ...],
  confidence: 0.85
}
```

- Skip re-parsing if recipe exists in cache and not expired
- Low-confidence parses flagged for exclusion

### Step 4: Match Scoring (LLM)

```
Input:  User ingredients + Recipe ingredients
Output: {
  coverage_score: 0.75,    // % of recipe ingredients user has
  missing: ["parmesan", "basil"],
  reasoning: "User has main ingredients, missing garnishes only"
}
```

### Step 5: Handoff to Meal Planner

- Top 10-15 scored recipes passed to Meal Plan Generator
- Includes: recipe data, coverage score, missing ingredients

## Architecture

### Backend Services (Python/FastAPI)

```
RecipeCollectionService
├── QueryGenerator          // LLM-based search query generation
├── YouTubeClient           // YouTube Data API v3 wrapper
├── InstagramClient         // Third-party API wrapper (RapidAPI)
├── DescriptionParser       // LLM-based ingredient extraction
├── RecipeMatcher           // LLM-based scoring against user ingredients
└── RecipeCache             // Persistent cache with TTL management
```

### Internal Endpoints (not user-facing)

```
POST /api/internal/recipes/search
  - Input: { ingredients: string[], user_id: string }
  - Output: { recipes: ScoredRecipe[] }
  - Called by Meal Plan Generator node in LangGraph

GET /api/internal/recipes/{id}
  - Retrieve cached recipe by ID

POST /api/internal/recipes/parse
  - Input: { source: string, source_id: string, description: string }
  - Output: { ingredients: string[], confidence: number }
```

### User-Facing Endpoints

```
GET /api/creators
  - List user's preferred creators

POST /api/creators
  - Add new preferred creator
  - Input: { source: "youtube" | "instagram", url: string }

DELETE /api/creators/{id}
  - Remove preferred creator
```

### LangGraph Integration

- Recipe Collection is a node between Ingredient Collection and Meal Plan Generation
- Receives ingredient session, outputs scored recipe pool
- Meal Plan Generator node consumes this pool

## Error Handling

### API Failures

| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| YouTube API down | HTTP error / timeout | Retry once, then proceed with Instagram only. Show user: "YouTube unavailable, using Instagram recipes" |
| Instagram service down | HTTP error / timeout | Retry once, then proceed with YouTube only. Show user: "Instagram unavailable, using YouTube recipes" |
| Both sources down | Both fail after retry | Show user: "Recipe sources unavailable. Please try again in a few minutes." Block meal planning. |
| Rate limit exceeded | 429 response | Use cached results only. If cache empty, show "High demand, please try again shortly" |

### Parsing Failures

| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| LLM API failure | OpenAI error | Retry 2x, then skip unparsed recipes (use only cached/already-parsed) |
| No ingredients extracted | Empty array returned | Exclude recipe from pool (unusable for matching) |
| Low confidence parse | confidence < 0.5 | Include but rank lower in results |

### Search Quality Issues

| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| Too few results | < 5 recipes returned | Broaden search with additional AI-generated queries |
| No matching recipes | All scores below threshold | Show user: "Couldn't find great matches. Try adding more ingredients?" |
| Preferred creators have no matches | 0 results from registered creators | Silently include general results (don't alarm user) |

## Testing Strategy

### Unit Tests

- Query generator: Verify LLM produces relevant search queries from ingredients
- Description parser: Test extraction from various description formats
  - Well-structured recipe with bullet points
  - Rambling description with ingredients buried in text
  - Non-recipe video (should return empty/low confidence)
- Match scorer: Verify scoring logic
  - Full coverage (user has all ingredients) → high score
  - Partial coverage → appropriate score with missing list
  - No overlap → low score

### Integration Tests (mock external APIs)

- YouTube client: Search, fetch video details, handle pagination
- Instagram client: Search via third-party service, parse response format
- Full pipeline: Ingredients → queries → search → parse → score → ranked results
- Cache behavior: Cache hit, cache miss, cache expiry

### API Contract Tests

- Third-party Instagram service: Verify response schema hasn't changed
- YouTube API: Verify quota handling and error responses

### E2E Tests

- Happy path: Ingredients → recipes found → passed to meal planner
- Degraded path: One source fails → other source used → meal plan still generated
- Creator priority: Registered creator's recipe ranks higher than equivalent match

### Manual Testing Checklist

- [ ] Test with real YouTube/Instagram API keys
- [ ] Test with various ingredient combinations (common, obscure)
- [ ] Verify creator registration flow works from settings
- [ ] Test cache invalidation after TTL

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Core model | On-demand search | Fresh results matching current ingredients |
| Creator priority | Boost registered creators | Personalized experience with trusted sources |
| Sources at launch | YouTube + Instagram | Two biggest recipe platforms |
| Instagram access | Third-party service (RapidAPI) | Avoids API restrictions and scraping issues |
| Search strategy | Multi-strategy (keywords + AI dishes) | Broader, more relevant results |
| User sees results? | No - direct to meal planner | Simpler UX, AI handles selection |
| Data extraction | AI description parsing | Handles natural language in video descriptions |
| Caching | Persistent with 30-day TTL | Balance freshness with API cost savings |
| Recipe data level | Standard (link, thumbnail, title, ingredients, creator) | Enough for matching without over-engineering |
| Matching algorithm | LLM-based scoring | Handles substitutions, partial matches, nuance |
| Result count | 10-15 top recipes to planner | Enough variety for weekly plan |
| API management | Smart batching + aggressive caching | Cost control |
| Error handling | Transparent to user | Honest about source availability |
