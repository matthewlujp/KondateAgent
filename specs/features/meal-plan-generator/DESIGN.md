---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/ARCHITECTURE.md#backend-patterns
  - ../../../specs/DOMAIN.md#mealplan
  - ../../../specs/DOMAIN.md#mealslot
  - ../../../specs/DOMAIN.md#refinementsession
status: implemented
---

# Design: Meal Plan Generator

Technical implementation of meal plan generation and refinement.

## Data Models

### MealPlan

```python
class MealPlan(BaseModel):
    id: str
    user_id: str
    ingredient_session_id: str
    status: Literal["draft", "active"]
    created_at: datetime
    slots: list[MealSlot]
```

### MealSlot

```python
class MealSlot(BaseModel):
    id: str
    day: DayOfWeek  # monday, tuesday, ..., sunday
    enabled: bool
    recipe_id: Optional[str]
    assigned_at: Optional[datetime]
    swap_count: int
```

### RefinementSession

```python
class RefinementSession(BaseModel):
    id: str
    meal_plan_id: str
    messages: list[ChatMessage]

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: Optional[list[dict]]
    timestamp: datetime
```

## Generation Pipeline

```
ScoredRecipes (10-15)
        ↓
┌───────────────────┐
│  MealPlanGenerator│ → LLM assigns recipes to days
└─────────┬─────────┘
          ↓
┌───────────────────┐
│  Slot Builder     │ → Creates MealSlot objects
└─────────┬─────────┘
          ↓
MealPlan with assigned slots
```

### LLM Assignment Prompt

```
You are a meal planning expert. Assign recipes to days.

Goals (priority order):
1. Ingredient efficiency - minimize waste
2. Variety - spread cuisines/proteins
3. Complexity balance - mix simple and complex

Rules:
- Assign each recipe to at most one day
- Don't repeat similar dishes on consecutive days
- Provide reasoning for each assignment
```

### Structured Output

```python
class RecipeAssignment(BaseModel):
    day: DayOfWeek
    recipe_id: str
    reasoning: str

class PlanAssignments(BaseModel):
    assignments: list[RecipeAssignment]
```

## Refinement System

### Tool-Calling Approach

LLM receives user message and decides which tool to call:

```python
# Available tools
swap_meal(day: str, criteria: Optional[str])
    # Replace day's meal
    # criteria: "quicker", "vegetarian", "different protein"

disable_day(day: str, reason: Optional[str])
    # Mark day as skipped

add_preference(type: Literal["avoid", "prefer"], value: str)
    # Save user preference

get_alternatives(day: str, count: int)
    # Show N alternatives without swapping
```

### Refinement Flow

```
User Message
     ↓
┌─────────────────┐
│ LLM with Tools  │ → Decides tool call(s)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Tool Execution  │ → Modifies plan
└────────┬────────┘
         ↓
┌─────────────────┐
│ Response Format │ → "Swapped Tuesday to..."
└────────┬────────┘
         ↓
Updated MealPlan + Response
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/meal-plans` | POST | Generate new plan |
| `/api/meal-plans/{id}` | GET | Get plan with recipes |
| `/api/meal-plans/{id}/chat` | POST | Refinement message |

### Generate Request/Response

```python
# Request
class GeneratePlanRequest(BaseModel):
    ingredient_session_id: str
    enabled_days: list[DayOfWeek]
    recipe_ids: list[str]

# Response
class MealPlanResponse(BaseModel):
    plan: MealPlan
    recipes: list[Recipe]  # Populated recipe data
```

### Chat Request/Response

```python
# Request
class ChatRequest(BaseModel):
    message: str

# Response
class ChatResponse(BaseModel):
    response: str
    plan: MealPlan
    tool_calls: list[dict]
    recipes: list[Recipe]
```

## Backend Services

```
MealPlanService
├── MealPlanGenerator       # LLM assignment
├── MealPlanRefinement      # Chat + tool-calling
├── MealPlanStore           # In-memory persistence
└── RecipePoolManager       # Access cached recipes
```

### MealPlanGenerator

```python
class MealPlanGenerator:
    async def generate(
        self,
        recipes: list[Recipe],
        enabled_days: list[DayOfWeek],
        user_ingredients: list[str],
    ) -> list[MealSlot]:
        # LLM structured output for assignments
        # Fallback: round-robin if LLM fails
```

### MealPlanRefinement

```python
class MealPlanRefinement:
    async def process_message(
        self,
        plan: MealPlan,
        message: str,
        recipes: list[Recipe],
    ) -> tuple[str, MealPlan, list[dict]]:
        # LLM with tool definitions
        # Execute tool calls
        # Return response + updated plan
```

## Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| LLM generation fails | OpenAI error | Fallback to round-robin |
| No suitable swap | Empty search result | Offer best available with tradeoff |
| Ambiguous request | No tool calls | Ask for clarification |
| Tool execution fails | Exception | Keep previous state, explain |

## Testing

### Unit Tests
- Generator: recipe assignment logic
- Slot builder: enabled/disabled handling
- Tool execution: each tool individually

### Integration Tests
- Full generation flow
- Refinement loop with tool calls
- State persistence across requests

### Tool-Calling Tests
- Intent classification accuracy
- Multi-intent handling
- Edge cases: "change the pasta one"

## Related Documents

- Original design: [Docs/plans/2026-01-26-meal-plan-generator-design.md](../../../Docs/plans/2026-01-26-meal-plan-generator-design.md)
