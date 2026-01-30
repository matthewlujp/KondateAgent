# Feature: Meal Plan Generator

## Purpose

Create an optimized weekly dinner plan and let users refine it through natural conversation.

## User Problem

Deciding what to cook each day is exhausting. Users want a complete week planned out that makes sense together - using their ingredients efficiently, providing variety, and matching their lifestyle.

## Behavior

### Plan Generation

1. User sees a week grid with toggle for each day
2. User disables days they don't need (eating out, leftovers)
3. User taps "Plan my meals!"
4. System assigns recipes to enabled days
5. User sees the complete weekly plan

### What Gets Optimized

The plan balances multiple goals:
- **Ingredient efficiency**: Use what you have, minimize shopping
- **Variety**: Different cuisines and proteins across the week
- **Complexity**: Mix quick meals and more involved cooking

### Plan Display

Each day shows:
- Recipe title and thumbnail
- Tap to see: cooking time, ingredients, link to full recipe

### Refinement via Chat

Users can adjust the plan by chatting naturally:
- "Change Tuesday to something lighter"
- "I don't want pasta twice this week"
- "Make Thursday quicker, I have a meeting"
- "Skip Wednesday, we're eating out"

The system swaps only the requested meals, keeping the rest intact.

### No Explicit Approval

- Plan is immediately usable after generation
- User keeps refining until satisfied
- No "approve" button needed

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| Too few recipes found | Show partial plan, explain gaps |
| Can't understand chat | "Try something like 'change Tuesday' or 'something quicker'" |
| No good replacement | Offer best available: "Closest I found is X - it's 25 mins instead of 15" |
| Conflicting request | "Can't find something both quick AND elaborate. Which matters more?" |

## Success Criteria

- Generate sensible plan in under 5 seconds
- Average user needs < 2 swaps to be satisfied
- Chat understands 90%+ of refinement requests
