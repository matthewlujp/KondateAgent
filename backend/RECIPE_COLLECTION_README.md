# Recipe Collection Feature - Setup & Usage

This document explains how to run and test the Recipe Collection feature.

## Overview

The Recipe Collection feature searches YouTube and Instagram for recipes based on user ingredients, parses video/post descriptions to extract ingredients, and scores recipes by how well they match available ingredients.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- API Keys:
  - OpenAI API key (for LLM parsing and matching)
  - YouTube Data API v3 key
  - Instagram RapidAPI key (optional)

## Setup

### 1. Install Dependencies

```bash
cd backend
uv sync
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-openai-key-here
YOUTUBE_API_KEY=your-youtube-api-key-here
INSTAGRAM_RAPIDAPI_KEY=your-rapidapi-key-here

# JWT Settings (for auth)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Getting API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy to `.env`

#### YouTube Data API v3 Key
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Copy to `.env`

#### Instagram RapidAPI Key (Optional)
1. Go to https://rapidapi.com/
2. Search for "Instagram" APIs (e.g., "Instagram Scraper API")
3. Subscribe to a plan (free tier available)
4. Copy your RapidAPI key to `.env`

**Note:** Instagram functionality is optional. The system will work with YouTube only if Instagram API is not configured.

## Running the Server

### Development Server

```bash
cd backend
uv run uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

### Check Server Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### View API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Running Tests

### Run All Tests

```bash
cd backend
uv run pytest -v
```

### Run Specific Test File

```bash
uv run pytest tests/test_ingredient_parser.py -v
```

### Run Tests with Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

## API Usage

### Authentication

Most user-facing endpoints require authentication. First, get a JWT token:

```bash
# Create a test token (for development)
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Use this token in subsequent requests:
```bash
curl -H "Authorization: Bearer eyJhbGc..." http://localhost:8000/api/creators
```

### Recipe Collection Endpoints

#### 1. Search for Recipes (Internal - No Auth Required)

```bash
curl -X POST http://localhost:8000/api/internal/recipes/search \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "ingredients": ["chicken breast", "tomatoes", "garlic", "pasta"],
    "max_results": 10
  }'
```

Response:
```json
{
  "recipes": [
    {
      "recipe": {
        "id": "uuid-here",
        "source": "youtube",
        "source_id": "dQw4w9WgXcQ",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "thumbnail_url": "https://i.ytimg.com/...",
        "title": "Easy Chicken Pasta Recipe",
        "creator_name": "Chef's Channel",
        "creator_id": "UCxxxxx",
        "extracted_ingredients": ["chicken breast", "pasta", "tomatoes", "garlic", "olive oil", "basil"],
        "duration": "PT10M30S",
        "posted_at": "2024-01-15T12:00:00Z",
        "cached_at": "2024-01-27T10:00:00Z",
        "cache_expires_at": "2024-02-26T10:00:00Z"
      },
      "coverage_score": 0.85,
      "missing_ingredients": ["basil", "olive oil"],
      "reasoning": "User has all main ingredients, missing only garnish and cooking oil"
    }
  ]
}
```

#### 2. Get Cached Recipe by ID

```bash
curl http://localhost:8000/api/internal/recipes/recipe-id-here
```

### Preferred Creators Endpoints (Require Auth)

#### 1. List User's Preferred Creators

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/creators
```

Response:
```json
[
  {
    "id": "creator-uuid",
    "user_id": "test-user",
    "source": "youtube",
    "creator_id": "UCxxxxx",
    "creator_name": "Chef's Channel",
    "added_at": "2024-01-27T10:00:00Z"
  }
]
```

#### 2. Add Preferred Creator

```bash
curl -X POST http://localhost:8000/api/creators \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "youtube",
    "url": "https://www.youtube.com/@gordonramsay"
  }'
```

Supported URL formats:
- YouTube: `youtube.com/@channelname`, `youtube.com/c/channelname`, `youtube.com/channel/UCxxxxx`
- Instagram: `instagram.com/username`

Response:
```json
{
  "creator": {
    "id": "new-creator-uuid",
    "user_id": "test-user",
    "source": "youtube",
    "creator_id": "gordonramsay",
    "creator_name": "gordonramsay",
    "added_at": "2024-01-27T10:30:00Z"
  },
  "message": "Added gordonramsay to your preferred creators"
}
```

#### 3. Delete Preferred Creator

```bash
curl -X DELETE http://localhost:8000/api/creators/creator-uuid \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response: `204 No Content`

## Testing the Full Pipeline

### Step-by-Step Test

1. **Start the server:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Get an auth token:**
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user"}' | jq -r '.access_token')
   ```

3. **Add a preferred creator (optional):**
   ```bash
   curl -X POST http://localhost:8000/api/creators \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "source": "youtube",
       "url": "https://www.youtube.com/@BabishCulinaryUniverse"
     }'
   ```

4. **Search for recipes:**
   ```bash
   curl -X POST http://localhost:8000/api/internal/recipes/search \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test-user",
       "ingredients": ["chicken", "rice", "broccoli"],
       "max_results": 5
     }' | jq
   ```

5. **List your preferred creators:**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/creators | jq
   ```

## Troubleshooting

### API Key Issues

**Error:** `"YouTube API key not configured"`
- **Solution:** Add `YOUTUBE_API_KEY` to your `.env` file

**Error:** `"Rate limit exceeded"` (429)
- **Solution:** YouTube API has daily quotas. Wait or use a different API key.

**Error:** `"API key invalid or quota exceeded"` (403)
- **Solution:** Check that your API key is valid and has the correct permissions.

### OpenAI Errors

**Error:** `"OpenAI API error"`
- **Solution:** Verify `OPENAI_API_KEY` is set correctly in `.env`
- Check you have credits available at https://platform.openai.com/usage

### No Recipes Found

**Issue:** Search returns empty results
- **Cause:** Ingredients too specific or obscure
- **Solution:** Try broader ingredients (e.g., "chicken" instead of "chicken breast supreme")

**Issue:** All recipes filtered out (low confidence)
- **Cause:** Search results aren't actual recipes (vlogs, reviews, etc.)
- **Solution:** This is expected behavior. Try different ingredient combinations.

### Instagram Not Working

**Issue:** Instagram results always empty
- **Cause 1:** Instagram RapidAPI key not configured
- **Solution:** Add `INSTAGRAM_RAPIDAPI_KEY` to `.env` (or skip Instagram)
- **Cause 2:** RapidAPI service endpoint doesn't match code
- **Solution:** Update `InstagramClient.BASE_URL` to match your RapidAPI service

## Architecture

### Pipeline Flow

```
User Ingredients
    ↓
QueryGenerator (LLM) → Search Queries
    ↓
[YouTube Search] + [Instagram Search] (parallel)
    ↓
DescriptionParser (LLM) → Extract Ingredients
    ↓
RecipeCache (30-day TTL)
    ↓
RecipeMatcher (LLM) → Score vs User Ingredients
    ↓
Top N Scored Recipes
```

### Key Components

- **Models**: `Recipe`, `PreferredCreator`
- **Stores**: `recipe_cache`, `creator_store` (in-memory, replace with DB in production)
- **Services**:
  - `QueryGenerator` - Generate search queries from ingredients
  - `YouTubeClient` - Search YouTube Data API v3
  - `InstagramClient` - Search Instagram via RapidAPI
  - `DescriptionParser` - Extract ingredients from descriptions
  - `RecipeMatcher` - Score recipes against user ingredients
  - `RecipeCollectionService` - Orchestrates full pipeline
- **Routers**:
  - `/api/internal/recipes/*` - Internal endpoints (no auth)
  - `/api/creators` - User-facing creator management (auth required)

## Next Steps

- [ ] Add database persistence (replace in-memory stores)
- [ ] Implement LangGraph integration for Meal Plan Generator
- [ ] Add rate limiting and request caching
- [ ] Implement the `/api/internal/recipes/parse` endpoint
- [ ] Add comprehensive integration tests
- [ ] Add monitoring and logging
- [ ] Optimize LLM costs (batch processing, caching)

## Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review logs for error details
3. Verify all API keys are correctly configured
4. Ensure you're using the correct endpoint (internal vs user-facing)
