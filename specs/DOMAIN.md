# DOMAIN.md

> **Layer 2**: WHAT we build (domain entities)

---

## Entity Overview

```
┌────────────────┐       ┌────────────────┐
│     User       │───────│PreferredCreator│
└────────────────┘       └────────────────┘
        │                        │
        │                        ▼
        │                ┌────────────────┐
        ▼                │     Recipe     │
┌────────────────┐       └────────────────┘
│IngredientSession│              │
└────────────────┘              │
        │                       │
        ▼                       ▼
┌────────────────┐       ┌────────────────┐
│   Ingredient   │       │    MealPlan    │
└────────────────┘       └────────────────┘
                                │
                                ▼
                         ┌────────────────┐
                         │    MealSlot    │
                         └────────────────┘
```

---

## Core Entities

### User

Represents a person using the application.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |

**Notes:**
- Currently minimal; authentication adds more fields later
- Referenced by all user-scoped entities

---

### Ingredient

A single ingredient the user has available.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| name | string | Normalized ingredient name |
| quantity | string | Amount (e.g., "2", "500g") |
| unit | string? | Unit of measurement |
| raw_input | string | Original user input |
| confidence | float [0-1] | Parsing confidence score |
| created_at | datetime | When parsed |

**Business Rules:**
- `name` should be normalized (lowercase, singular)
- `confidence < 0.7` may need user confirmation
- `raw_input` preserved for debugging/reprocessing

**Example:**
```json
{
  "id": "abc-123",
  "name": "chicken breast",
  "quantity": "2",
  "unit": "pieces",
  "raw_input": "2 chicken breasts",
  "confidence": 0.95
}
```

---

### IngredientSession

A collection of ingredients for one meal planning session.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| user_id | string | Owner |
| ingredients | Ingredient[] | Parsed ingredients |
| status | enum | `in_progress` / `confirmed` / `used` |
| created_at | datetime | Session start |
| updated_at | datetime | Last modification |

**Status Transitions:**
```
in_progress ──▶ confirmed ──▶ used
     │              │
     └──────────────┘ (can add more before confirming)
```

**Business Rules:**
- One active session per user at a time
- `confirmed` triggers recipe search
- `used` after meal plan generated

---

### PreferredCreator

A recipe source (YouTube channel/Instagram account) the user follows.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| user_id | string | Owner |
| source | enum | `youtube` / `instagram` |
| creator_id | string | Platform-specific ID |
| creator_name | string | Display name |
| added_at | datetime | When added |

**Business Rules:**
- User can have multiple creators per source
- `creator_id` is unique per source per user
- Recipes fetched from all user's creators

**Example:**
```json
{
  "id": "xyz-789",
  "source": "youtube",
  "creator_id": "UC1234abcd",
  "creator_name": "Joshua Weissman"
}
```

---

### Recipe

A recipe from an external source, cached locally.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Internal identifier |
| source | enum | `youtube` / `instagram` |
| source_id | string | Platform video/post ID |
| url | string | Direct link to content |
| thumbnail_url | string | Preview image |
| title | string | Recipe title |
| creator_name | string | Who made it |
| creator_id | string | Creator's platform ID |
| extracted_ingredients | string[] | Parsed from description |
| raw_description | string | Original description |
| duration | string? | Video length (YouTube) |
| posted_at | datetime | Original post date |
| cached_at | datetime | When we cached it |
| cache_expires_at | datetime | TTL for refresh |

**Business Rules:**
- `extracted_ingredients` parsed from description by LLM
- Cache TTL typically 24 hours
- `source_id` + `source` is unique

**Derived Properties:**
- `coverage_score`: % of user ingredients matched (calculated at search time)

---

### MealPlan

A weekly dinner plan for a user.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| user_id | string | Owner |
| ingredient_session_id | string | Source ingredients |
| status | enum | `draft` / `active` |
| created_at | datetime | When generated |
| slots | MealSlot[] | Day assignments |

**Status Transitions:**
```
draft ──▶ active
  │          │
  └──────────┘ (regenerate creates new draft)
```

**Business Rules:**
- `draft` during generation/refinement
- `active` when user starts using
- One active plan per user at a time

---

### MealSlot

A single day's meal assignment within a plan.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| day | DayOfWeek | `monday` through `sunday` |
| enabled | boolean | User wants to plan this day |
| recipe_id | string? | Assigned recipe (null if disabled) |
| assigned_at | datetime? | When recipe was assigned |
| swap_count | integer | Times user swapped this slot |

**DayOfWeek Enum:**
```
monday | tuesday | wednesday | thursday | friday | saturday | sunday
```

**Business Rules:**
- `enabled=false` means user is skipping this day
- `recipe_id` null when `enabled=false`
- `swap_count` tracks refinement activity

---

### ChatMessage

A message in the meal plan refinement conversation.

| Field | Type | Description |
|-------|------|-------------|
| role | enum | `user` / `assistant` |
| content | string | Message text |
| tool_calls | object[]? | Actions taken (assistant only) |
| timestamp | datetime | When sent |

**Business Rules:**
- `tool_calls` records what system did (swap_meal, etc.)
- Messages belong to a RefinementSession

---

### RefinementSession

A chat session for refining a meal plan.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| meal_plan_id | string | Plan being refined |
| messages | ChatMessage[] | Conversation history |

**Business Rules:**
- One session per meal plan
- Session resets on new plan generation
- History used for context in LLM calls

---

## Value Objects

These are not persisted entities but important domain concepts:

### CoverageScore
```typescript
{
  score: number;        // 0-1, percentage of ingredients matched
  matched: string[];    // Ingredients used by recipe
  missing: string[];    // Ingredients recipe needs but user lacks
}
```

### RecipeAssignment
```typescript
{
  day: DayOfWeek;
  recipe_id: string;
  reasoning: string;    // Why AI chose this assignment
}
```

---

## Relationships

| From | To | Relationship |
|------|----|--------------|
| User | IngredientSession | 1:many (one active) |
| User | PreferredCreator | 1:many |
| User | MealPlan | 1:many (one active) |
| IngredientSession | Ingredient | 1:many |
| IngredientSession | MealPlan | 1:1 |
| PreferredCreator | Recipe | 1:many (fetched) |
| MealPlan | MealSlot | 1:7 |
| MealSlot | Recipe | many:1 |
| MealPlan | RefinementSession | 1:1 |
| RefinementSession | ChatMessage | 1:many |

---

## Invariants

Rules that must always be true:

1. **One active session per user**: User can have at most one `IngredientSession` with status `in_progress`

2. **Enabled slots have recipes**: If `MealSlot.enabled=true` and plan is `active`, `recipe_id` must be set

3. **Disabled slots are empty**: If `MealSlot.enabled=false`, `recipe_id` must be null

4. **Recipes reference valid creators**: `Recipe.creator_id` matches a `PreferredCreator` the user has added

5. **Plan ties to session**: `MealPlan.ingredient_session_id` must reference a valid `IngredientSession`

---

## References

- Backend models: `backend/app/models/`
- Frontend types: `frontend/src/types/`
- Feature specs inherit these entities
