# Mobile-Friendly Meal Plan UI Design

**Date**: 2026-01-29
**Status**: Draft
**Author**: Collaborative design session

## Overview

Redesign the meal plan interface to be mobile-first while still supporting desktop users. The current two-page layout with side-by-side grid and chat panel is too wide for smartphone users.

## Key Changes

1. **Single scrollable page** - Consolidate ingredients, recipes, and meal plan into one page
2. **Vertical meal cards** - Replace grid with expandable cards in a vertical list
3. **Floating chat FAB** - Hide chat behind a floating action button with popup
4. **Independent sections** - Allow editing upstream steps without auto-invalidating downstream

## Page Structure

```
┌─────────────────────────────────┐
│  Header: "Plan Your Meals"      │
├─────────────────────────────────┤
│  § Ingredients                  │  ← Collapsible section
│    [Voice/Text input]           │
│    [Ingredient list]            │
│    [🔄 Re-search Recipes]       │
├─────────────────────────────────┤
│  § Recipes Found (12)           │  ← Collapsible section
│    [Recipe cards grid]          │
│    [🔄 Search Again]            │
├─────────────────────────────────┤
│  § Your Meal Plan               │  ← Collapsible section
│    [Day toggles]                │
│    [Meal cards - vertical]      │
│    [🔄 Regenerate Plan]         │
└─────────────────────────────────┘

                            ┌────┐
                            │ 💬 │  ← Fixed position FAB
                            └────┘     (bottom-right, always visible)
```

### Section Behavior
- Each section starts expanded
- User can collapse/expand any section via header tap
- Sections maintain their state independently
- Refresh buttons always visible at section bottom

### Initial Load Flow
1. Ingredients section: empty, ready for input
2. Recipes section: hidden until first search completes
3. Meal Plan section: hidden until plan is generated

## Expandable Meal Cards

Cards displayed in a **vertical stack** (single column on mobile, 2 columns on tablet+).

### Collapsed State (default)
```
┌─────────────────────────────────────┐
│ ┌──────┐  Monday                  ▼ │
│ │ 🖼️   │  Chicken Teriyaki Bowl    │
│ │thumb │  @CookingWithDog          │
│ └──────┘                            │
└─────────────────────────────────────┘
```
- Thumbnail (small, ~60x60)
- Day label (prominent)
- Recipe title (truncated if long)
- Creator name
- Chevron indicating expandable

### Expanded State (tap to toggle)
```
┌─────────────────────────────────────┐
│ ┌──────┐  Monday                  ▲ │
│ │ 🖼️   │  Chicken Teriyaki Bowl    │
│ │thumb │  @CookingWithDog          │
│ └──────┘                            │
├─────────────────────────────────────┤
│ ⏱️ 30 min                           │
│                                     │
│ 🥗 Ingredients:                     │
│ • chicken breast • soy sauce        │
│ • mirin • rice • broccoli           │
│                                     │
│ 📝 Instructions:                    │
│ 1. Slice chicken into strips...     │
│ 2. Heat pan with oil...             │
│ [View full recipe →]                │
└─────────────────────────────────────┘
```
- Cooking time estimate
- Full ingredient list
- Instructions preview (first 2-3 steps)
- Link to full recipe source

### Expansion Behavior
- **Independent expansion** - Each card can be expanded/collapsed independently
- Multiple cards can be open simultaneously (for comparing recipes)

### Disabled/Skipped Days
```
┌─────────────────────────────────────┐
│        Saturday · Skipped           │
└─────────────────────────────────────┘
```

## Chat FAB & Popup

### Mobile (< 1024px)

**FAB Button:**
- 56x56px, fixed position bottom-right (`bottom-6 right-6`)
- `shadow-lg`, `terra-500` background
- Always visible while scrolling
- Hides when bottom sheet is open

**Bottom Sheet (on tap):**
```
┌─────────────────────────────────────┐
│ ━━━━━  (drag handle)                │
│                                     │
│  Refine Your Plan            [✕]   │
├─────────────────────────────────────┤
│                                     │
│  [Chat messages area]               │
│  - scrollable                       │
│  - ~70% viewport height             │
│                                     │
├─────────────────────────────────────┤
│ ┌─────────────────────────┐ [Send] │
│ │ Ask to swap a meal...   │        │
│ └─────────────────────────┘        │
└─────────────────────────────────────┘
```
- Semi-transparent backdrop overlay
- Closable via: X button, drag down, or backdrop tap

### Desktop (≥ 1024px)

**Collapsible Sidebar:**
```
┌──────────────────────┬─────────────┐
│                      │ Refine Plan │
│  Main content        │             │
│  (sections)          │ [messages]  │
│                      │             │
│                      │ [input]     │
└──────────────────────┴─────────────┘
```
- ~320px wide sidebar on right
- Collapse button to hide sidebar (shows FAB when collapsed)
- Starts collapsed by default, FAB visible
- Opening sidebar hides FAB

## Section Independence & Refresh

Each section operates independently with its own refresh action.

### Section 1: Ingredients
```
┌─────────────────────────────────────┐
│ § Ingredients                    ─  │
├─────────────────────────────────────┤
│ [Voice input / Text input]          │
│                                     │
│ • 3 chicken breasts         [✕]    │
│ • 2 cups rice               [✕]    │
│ • soy sauce                 [✕]    │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │  🔄  Re-search Recipes          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Section 2: Recipes Found
```
┌─────────────────────────────────────┐
│ § Recipes Found (12)             ─  │
├─────────────────────────────────────┤
│ [Recipe preview cards...]           │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │  🔄  Search Again               │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Section 3: Meal Plan
```
┌─────────────────────────────────────┐
│ § Your Meal Plan                 ─  │
├─────────────────────────────────────┤
│ [Day toggles: M T W T F S S]        │
│                                     │
│ [Expandable meal cards...]          │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │  🔄  Regenerate Plan            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### State Preservation Rules
- Editing ingredients does NOT auto-clear recipes or plan
- "Re-search Recipes" replaces recipe list but keeps meal plan intact
- "Regenerate Plan" creates new plan from current recipes
- Chat refinements only affect specific slots

## Edge Cases & State Indicators

### Loading States
Each refresh button shows inline loading:
```
┌─────────────────────────────────────┐
│  ⟳  Searching recipes...           │
└─────────────────────────────────────┘
```
- Spinner + text
- Button disabled during operation

### Empty States

**Recipes section (before first search):**
```
┌─────────────────────────────────────┐
│ § Recipes                           │
├─────────────────────────────────────┤
│     🍳                              │
│     Add ingredients above and       │
│     tap "Re-search Recipes"         │
└─────────────────────────────────────┘
```

**Meal Plan section (before first generation):**
```
┌─────────────────────────────────────┐
│ § Your Meal Plan                    │
├─────────────────────────────────────┤
│     📅                              │
│     Search for recipes first,       │
│     then generate your plan         │
└─────────────────────────────────────┘
```

### Button States
- "Re-search Recipes" disabled if no ingredients
- "Generate Plan" disabled if no recipes found
- "Regenerate Plan" disabled if no enabled days selected

### Chat Context
- Chat messages persist within the session
- Scrolling back to edit ingredients doesn't clear chat
- Chat currently handles meal swaps only

### URL Handling
- Single route: `/` (home page becomes the unified flow)
- Session ID stored in sessionStorage for refresh recovery
- Remove `/meal-plan` route (or redirect to `/`)

## Implementation Notes

### Files to Modify
- `frontend/src/pages/IngredientCollectionPage.tsx` - Expand to include all sections
- `frontend/src/components/MealSlotCard.tsx` - Add expandable behavior
- `frontend/src/components/ChatPanel.tsx` - Convert to FAB + bottom sheet (mobile) / collapsible sidebar (desktop)

### Files to Remove/Deprecate
- `frontend/src/pages/MealPlanPage.tsx` - Functionality merged into main page

### New Components Needed
- `CollapsibleSection.tsx` - Reusable section wrapper with collapse toggle
- `ChatFAB.tsx` - Floating action button for chat
- `ChatBottomSheet.tsx` - Mobile chat popup
- `ExpandableMealCard.tsx` - New meal card with expand/collapse

### Responsive Breakpoints
- Mobile: < 768px (single column, FAB + bottom sheet)
- Tablet: 768px - 1023px (2 column cards, FAB + bottom sheet)
- Desktop: ≥ 1024px (2 column cards, collapsible sidebar)

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Page structure | Single scrollable page | Better mobile UX, no navigation interruption |
| Day selection | Inline with toggles | User control preserved, no extra step |
| Meal card layout | Vertical stack | Mobile-friendly, easy scanning |
| Card expansion | Independent | Allows comparing multiple recipes |
| Chat trigger | Floating FAB | Unobtrusive, familiar pattern |
| Chat display (mobile) | Bottom sheet | Standard mobile pattern, large touch area |
| Chat display (desktop) | Collapsible sidebar | Efficient use of wide screens |
| Section refresh | Always-visible buttons | Predictable, discoverable |
| State independence | Manual refresh only | No surprise data loss |
