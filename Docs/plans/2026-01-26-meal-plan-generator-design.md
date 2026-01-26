# Meal Plan Generator & Refinement Feature Design

**Date**: 2026-01-26
**Status**: Approved
**Author**: Collaborative design session

## Overview

Generate an optimized weekly dinner plan from collected recipes, then allow users to refine it through natural text chat until they're ready to shop.

## Plan Structure

- 7 dinner slots (one per day)
- User can disable specific days via toggle UI before generating ("Skip Saturday")
- Plan covers enabled days only

## User Flow

### Generation Flow

1. User finishes ingredient collection, sees week grid with toggle controls
2. User disables any days they don't need (eating out, leftovers, etc.)
3. User taps "Plan my meals!"
4. Recipe Collection runs (behind the scenes)
5. Meal Plan Generator receives 10-15 scored recipes
6. AI selects optimal recipes for enabled days
7. User sees proposed meal plan with progressive detail (minimal → rich on tap)

### Refinement Flow

1. Plan is immediately "active" - no explicit approval needed
2. User chats to refine: "Change Tuesday" / "Something quicker for Thursday"
3. System makes targeted swaps, keeps rest of plan intact
4. User can keep refining until they tap "Show shopping list"
5. Shopping list generation locks the plan

## Data Model

### Meal Plan

```typescript
interface MealPlan {
  id: string;
  user_id: string;
  ingredient_session_id: string;
  status: "draft" | "active" | "locked";
  created_at: timestamp;
  locked_at?: timestamp;
  slots: MealSlot[];
}

interface MealSlot {
  id: string;
  day: "monday" | "tuesday" | ... | "sunday";
  enabled: boolean;           // false if user disabled this day
  recipe_id?: string;         // null if disabled
  recipe: Recipe;             // populated from cache
  assigned_at: timestamp;
  swap_count: number;         // how many times user swapped this slot
}
```

### User Preferences

```typescript
interface UserPreferences {
  user_id: string;
  explicit: {
    avoid_ingredients: string[];    // "no fish", "allergic to nuts"
    cuisine_preferences: string[];  // "love Italian", "no spicy"
    max_prep_time?: number;         // minutes
  };
  learned: {
    rejected_patterns: string[];    // inferred from swap history
    preferred_creators: string[];   // from feedback
    variety_tolerance: number;      // how much repetition is ok
  };
  updated_at: timestamp;
}
```

### Chat Session

```typescript
interface RefinementSession {
  id: string;
  meal_plan_id: string;
  messages: ChatMessage[];
  started_at: timestamp;
  ended_at?: timestamp;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tool_calls?: ToolCall[];    // actions taken
  timestamp: timestamp;
}
```

## AI Optimization

### Initial Plan Generation

```
Input:  10-15 scored recipes + enabled days + user preferences
        ↓
LLM Optimization Goals (balanced, adapts over time):
  1. Ingredient efficiency - minimize waste and shopping
  2. Variety - spread cuisines/proteins across week
  3. Complexity balance - easier meals on busy days
  4. User preferences - explicit rules + learned patterns
        ↓
Output: Assigned recipe per enabled day
```

### Refinement Tool Set

```typescript
// Tools available to LLM during chat refinement

swap_meal(day: string, criteria?: string)
  // Replace specific day's meal
  // criteria: "quicker", "vegetarian", "different protein"
  // Tries recipe pool first, searches fresh if needed

disable_day(day: string, reason?: string)
  // Mark day as skipped after initial generation

add_preference(type: "avoid" | "prefer", value: string)
  // Save explicit preference: "avoid fish", "prefer quick meals"

get_alternatives(day: string, count: number)
  // Show N alternatives for a specific day without swapping yet
```

### Tool Execution Flow

1. User message received
2. LLM decides which tool(s) to call based on intent
3. Tool executes, returns result
4. LLM formulates response: "Swapping Tuesday's meal..." + updated plan shown
5. If tool fails (no good match), LLM explains tradeoff with best available option

## Architecture

### LangGraph Workflow

```
                    ┌─────────────────┐
                    │   Ingredient    │
                    │   Collection    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Recipe      │
                    │   Collection    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Meal Plan     │
                    │   Generator     │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │                             │
              │    Refinement Loop          │◄──┐
              │    (Chat + Tool Calling)    │   │
              │                             │───┘
              └──────────────┬──────────────┘
                             │ user taps "Shopping List"
                    ┌────────▼────────┐
                    │  Shopping List  │
                    │   Generator     │
                    └─────────────────┘
```

### Backend Components

```
MealPlanService
├── PlanGenerator         // Initial plan creation with LLM
├── RefinementAgent       // Chat processing with tool-calling
├── PreferenceManager     // Explicit + learned preference storage
├── RecipePoolManager     // Access to scored recipes, triggers fresh search
└── PlanStateManager      // Draft → Active → Locked transitions
```

### Endpoints

```
POST /api/meal-plans
  - Input: { ingredient_session_id, disabled_days: string[] }
  - Output: { meal_plan: MealPlan }

POST /api/meal-plans/{id}/chat
  - Input: { message: string }
  - Output: { response: string, updated_plan: MealPlan, tools_called: ToolCall[] }

POST /api/meal-plans/{id}/lock
  - Locks plan, returns shopping list
  - Output: { shopping_list: ShoppingList }

GET /api/preferences
PUT /api/preferences
  - Manage explicit user preferences
```

## Error Handling

### Plan Generation Errors

| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| Too few recipes from search | < 3 usable recipes | "I found limited options for your ingredients. Here's what I can suggest..." + show partial plan with empty slots |
| No recipes match preferences | All filtered out by preferences | "Your preferences filtered out all options. Want to relax [specific preference] for this week?" |
| LLM generation failure | OpenAI error | Retry 2x, then "Having trouble planning right now. Try again in a moment." |

### Refinement Errors

| Scenario | Detection | System Behavior |
|----------|-----------|-----------------|
| Can't understand feedback | LLM returns no tool calls | "I didn't quite get that. Try something like 'change Tuesday' or 'something quicker for Wednesday'" |
| No suitable replacement | Pool empty + fresh search fails | Best effort: "Closest I found is [recipe] - it's 25 mins instead of 15. Want to try it?" |
| Conflicting requests | User asks for impossible combo | "I can't find something that's both quick AND elaborate. Which matters more?" |
| Tool execution failure | API/DB error | "Something went wrong updating the plan. Your previous version is still there - try again?" |

### State Recovery

| Scenario | System Behavior |
|----------|-----------------|
| User closes app mid-refinement | Plan persists in current state, chat history saved |
| User returns after days | Show current plan, chat starts fresh but preferences retained |
| Accidental lock (shopping list) | No unlock - but could add "Edit plan" that clears shopping list |

## Testing Strategy

### Unit Tests

- Plan generator: Verify LLM assigns recipes to enabled days only
- Slot toggling: Disabled days get no recipe, enabled days do
- Tool execution: Each tool (swap_meal, disable_day, add_preference) works correctly
- Preference merging: Explicit + learned preferences combine correctly
- State transitions: draft → active → locked flow

### Integration Tests

- Full generation flow: Ingredients → recipes → plan with correct assignments
- Refinement loop: User message → tool call → updated plan
- Pool-then-search: Swap tries pool first, falls back to fresh search
- Preference persistence: Preferences saved, applied to next planning session

### Tool-Calling Tests

- Intent classification: "Change Tuesday" → swap_meal(tuesday)
- Multi-intent: "Skip Wednesday and make Thursday quicker" → two tool calls
- Ambiguous input: Verify graceful fallback to clarification
- Edge cases: "Change the pasta one" (needs recipe identification)

### E2E Tests (Playwright)

- Happy path: Generate plan → chat to swap one meal → approve → shopping list
- Multi-swap: Swap 3 different days in one session
- Preference flow: Set explicit preference → verify it affects next plan
- Lock behavior: After shopping list, verify plan is not editable

### Manual Testing Checklist

- [ ] Natural language variations ("swap", "change", "replace", "don't want")
- [ ] Preference conflicts and tradeoff explanations
- [ ] Plan display on various mobile screen sizes
- [ ] Chat responsiveness and streaming feel
- [ ] Day toggle UI usability

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plan structure | 7 dinners, toggleable days | Simple scope, user controls what to plan |
| Slot disabling | Quick toggle UI before generation | Visual, fast, no typing needed |
| Optimization | Balanced + learns over time | Start sensible, improve with usage |
| Plan display | Progressive disclosure | Clean overview, details on demand |
| Feedback scope | Full conversational | Natural, flexible, handles any request |
| Update strategy | Targeted swap only | Predictable, no surprise changes |
| Replacement source | Pool first, then fresh search | Efficient, flexible when needed |
| Conversation model | Session-based, preferences saved | Context during session, clean starts |
| Preference learning | Explicit + implicit | User control + automatic improvement |
| Finalization | Soft acceptance | Low friction, no explicit approval |
| Lock trigger | Shopping list generation | Clear commitment point |
| Chat processing | LLM with tool-calling | Clean intent → action mapping |
| Response style | Action + result | Clear what happened |
| Failure handling | Best effort with tradeoff | Keep moving, be transparent |
