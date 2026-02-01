# Feature: Recipe Collection

## Purpose

Find recipes that match what the user has available, from creators they trust.

## User Problem

Users want meal ideas that actually use their ingredients, not random recipes requiring a whole shopping trip. They also prefer recipes from creators whose style they know and trust.

## Behavior

### Invisible to User

Recipe collection happens automatically behind the scenes:
1. User confirms their ingredients
2. System finds matching recipes (user sees loading state)
3. Results feed directly into meal plan generation
4. User only sees the final meal plan

### What Gets Searched

- **YouTube**: Recipe videos from cooking channels
- **Instagram**: Recipe posts from food accounts
- **Priority**: User's registered creators searched first

### Matching Logic

Recipes are scored by how well they match user's ingredients:
- **High match**: User has most ingredients needed
- **Medium match**: User has main ingredients, missing some
- **Low match**: Requires significant shopping

### Creator Priority

When user has registered favorite creators:
- Their recipes appear first in results
- Still includes other creators for variety
- User can add creators from Settings

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| No matching recipes | "Couldn't find great matches. Try adding more ingredients?" |
| YouTube unavailable | Use Instagram only, note in UI |
| Instagram unavailable | Use YouTube only, note in UI |
| Both unavailable | "Recipe sources unavailable. Try again shortly." |
| No registered creators | Search general recipe channels |

## Success Criteria

- Find 10-15 relevant recipes within 10 seconds
- At least 50% of results use majority of user's ingredients
- Registered creator recipes appear in top results
