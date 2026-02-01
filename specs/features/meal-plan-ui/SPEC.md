# Feature: Meal Plan UI

## Purpose

Display the weekly meal plan in a mobile-friendly way and provide easy access to chat refinement.

## User Problem

Users are often on their phone in the kitchen. They need to see their meal plan at a glance, get details when needed, and easily make changes - all with one hand while the other holds a pot or ingredient.

## Behavior

### Single-Page Layout

Everything on one scrollable page:

1. **Ingredients** - What user has available
2. **Recipes** - Matching recipes found (after search)
3. **Meal Plan** - The weekly plan (after generation)

Each section is collapsible to reduce clutter.

### Meal Plan Display

**Week at a Glance:**
- 7 days shown in a vertical list
- Each day shows: day name, recipe title, small thumbnail
- Disabled days shown as "Skipped"

**Tap for Details:**
- Tap any day to expand
- Expanded view shows:
  - Larger thumbnail
  - Cooking time
  - Full ingredient list
  - Link to original recipe
- Tap again to collapse
- Only one day expanded at a time

### Chat Refinement

**Opening Chat:**
- Floating button (FAB) in bottom-right corner
- Shows chat icon
- Tap to open chat interface

**Mobile Chat (Bottom Sheet):**
- Slides up from bottom
- Takes half the screen
- Messages scroll up, input at bottom
- Close by tapping X or swiping down

**Desktop Chat (Sidebar):**
- Opens as sidebar panel
- Doesn't cover main content

### Interactions

| Action | Result |
|--------|--------|
| Tap meal card | Expand to show details |
| Tap expanded card | Collapse back |
| Tap chat FAB | Open chat interface |
| Send chat message | Process refinement, update plan |
| Swipe section header | Collapse/expand section |

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| Plan not generated yet | Show "Generate Plan" button instead |
| Recipe has no thumbnail | Show placeholder image |
| Chat message fails | Keep message, show retry option |
| Very long ingredient list | Truncate with "Show more" |

## Success Criteria

- All interactions work one-handed on mobile
- Plan loads and displays in under 2 seconds
- Chat opens instantly (< 200ms)
- Touch targets are at least 44x44px
