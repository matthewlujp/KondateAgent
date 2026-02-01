# ARCHITECTURE.md

> **Layer 1**: HOW we build

---

## Technology Stack

### Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | FastAPI | Async-native, automatic OpenAPI docs, Pydantic integration |
| AI | OpenAI GPT-4o-mini | Structured outputs, cost-effective, fast |
| Package Manager | uv | Fast, reliable Python dependency management |
| Data Models | Pydantic | Type-safe, serialization built-in |

### Frontend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | React 18 | Mature ecosystem, component model |
| Build Tool | Vite | Fast HMR, modern bundling |
| Language | TypeScript | Type safety, better IDE support |
| Styling | Tailwind CSS | Utility-first, mobile-responsive |
| State | TanStack Query | Server state management, caching |
| Routing | React Router | Standard, simple |

### External APIs
| Service | Purpose |
|---------|---------|
| OpenAI | Ingredient parsing, meal plan generation, chat refinement |
| YouTube Data API | Recipe video metadata, channel info |
| Instagram Graph API | Recipe post metadata (future) |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, middleware, routers
│   │   ├── config.py         # Settings from environment
│   │   ├── auth.py           # Auth utilities (simple user ID)
│   │   ├── models/           # Pydantic data models
│   │   │   ├── ingredient.py
│   │   │   ├── recipe.py
│   │   │   └── meal_plan.py
│   │   ├── routers/          # API endpoints by domain
│   │   │   ├── ingredients.py
│   │   │   ├── recipes.py
│   │   │   ├── creators.py
│   │   │   └── meal_plans.py
│   │   └── services/         # Business logic
│   │       ├── ingredient_parser.py
│   │       ├── youtube_client.py
│   │       ├── recipe_matcher.py
│   │       ├── meal_plan_generator.py
│   │       └── ...
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Root, routing
│   │   ├── api/              # API client functions
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Route-level components
│   │   ├── hooks/            # Custom React hooks
│   │   └── types/            # TypeScript interfaces
│   └── test/
├── specs/                    # This documentation
│   ├── PRINCIPLES.md         # Why we build
│   ├── ARCHITECTURE.md       # How we build
│   └── DOMAIN.md             # What we build
├── Docs/plans/               # Feature design documents
└── CLAUDE.md                 # AI assistant instructions
```

---

## API Design

### Principles

1. **RESTful Resources**: Standard CRUD where applicable
2. **Session-Based**: Operations scoped to user sessions
3. **Idempotent**: Safe to retry failed requests

### Base URL
```
http://localhost:8000/api
```

### Endpoints Overview

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| **Ingredients** |||
| POST | `/ingredients/parse` | Parse natural language to ingredients |
| GET | `/ingredients/session/{id}` | Get session ingredients |
| POST | `/ingredients/session/{id}/confirm` | Confirm ingredient list |
| **Creators** |||
| GET | `/creators` | List user's preferred creators |
| POST | `/creators` | Add a creator |
| DELETE | `/creators/{id}` | Remove a creator |
| **Recipes** |||
| POST | `/recipes/search` | Search recipes from creators |
| GET | `/recipes/session/{id}` | Get cached recipes for session |
| **Meal Plans** |||
| POST | `/meal-plans` | Generate new plan |
| GET | `/meal-plans/{id}` | Get plan with recipes |
| POST | `/meal-plans/{id}/chat` | Refinement chat message |

### Response Format

All responses follow:
```json
{
  "data": { ... },      // Resource or array
  "error": null         // Or error message
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (validation failed) |
| 404 | Resource not found |
| 422 | Unprocessable (e.g., no recipes found) |
| 500 | Server error (retry safe) |

---

## Architecture Patterns

### Backend Patterns

#### Service Layer
Business logic lives in `services/`, not routers. Routers handle HTTP concerns only.

```python
# Router: HTTP layer
@router.post("/parse")
async def parse(request: ParseRequest):
    result = await ingredient_parser.parse(request.text)
    return {"data": result}

# Service: Business logic
class IngredientParser:
    async def parse(self, text: str) -> list[Ingredient]:
        # LLM call, validation, normalization
```

#### LLM Integration
All LLM calls use OpenAI's structured outputs:

```python
response = await openai_client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=ExpectedModel,  # Pydantic model
)
```

Benefits:
- Type-safe responses
- Automatic validation
- Consistent error handling

#### In-Memory Storage
Currently using in-memory stores (dict-based) for simplicity:

```python
class SessionStore:
    _sessions: dict[str, IngredientSession] = {}
```

Future: Replace with PostgreSQL when persistence needed.

### Frontend Patterns

#### API Layer
All API calls centralized in `src/api/`:

```typescript
// api/mealPlans.ts
export async function generatePlan(request: GeneratePlanRequest): Promise<MealPlan> {
  const response = await client.post('/meal-plans', request);
  return response.data;
}
```

#### Server State with TanStack Query
```typescript
const { data: plan, isLoading } = useQuery({
  queryKey: ['mealPlan', planId],
  queryFn: () => getMealPlan(planId),
});
```

#### Component Composition
- Pages compose components
- Components are self-contained with their own state
- Shared state lifted to pages, passed via props

---

## Data Flow

### Meal Planning Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │────▶│  Ingredients │────▶│   Recipes   │
│   Input     │     │   Parsing    │     │   Search    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  Ingredient  │     │   Recipe    │
                    │   Session    │     │   Cache     │
                    └──────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Meal Plan  │
                                        │  Generator  │
                                        └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Refinement  │◀──┐
                                        │    Chat     │───┘
                                        └─────────────┘
```

### State Management

| Data | Storage | Lifetime |
|------|---------|----------|
| Ingredients | Backend session | Until confirmed |
| Recipes | Backend cache | 24 hours |
| Meal Plan | Backend store | Until new plan |
| Chat History | Backend session | Per refinement |
| UI State | React state | Per page visit |
| API Cache | TanStack Query | 5 minutes |

---

## Security

### Current (Development)
- Simple user_id header for identification
- CORS restricted to localhost:5173
- No authentication

### Future (Production)
- JWT tokens for authentication
- Rate limiting on API endpoints
- Input sanitization for LLM prompts
- API key rotation

---

## Testing Strategy

### Backend
```bash
uv run pytest -n auto          # Run all tests in parallel
uv run pytest tests/test_x.py  # Run specific file
```

- Unit tests for services
- Integration tests for routers
- Mocked external API calls

### Frontend
```bash
npm test                       # Run all tests
npm test -- Component.test.tsx # Run specific file
```

- Component tests with React Testing Library
- API mocking with MSW (Mock Service Worker)

---

## Development Workflow

### Commands

```bash
# Backend
cd backend
uv sync                                    # Install deps
uv run uvicorn app.main:app --reload       # Start server

# Frontend
cd frontend
npm install                                # Install deps
npm run dev                                # Start dev server

# Testing
uv run pytest -n auto                      # Backend tests
npm test                                   # Frontend tests
```

### Environment Variables

Backend `.env`:
```
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
LOG_LEVEL=DEBUG
```

Frontend `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

---

## References

- Features must comply with this architecture
- New technologies require RFC in `specs/rfcs/`
- Pattern changes require update to this document
