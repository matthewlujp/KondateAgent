# Ingredient Collection Feature Design

**Date**: 2026-01-25
**Status**: Approved
**Author**: Collaborative design session

## Overview

Enable users to quickly and naturally communicate what ingredients they have available, creating the foundation for intelligent meal planning.

## User Flow

1. User opens app, chooses "Start fresh" or "Update last list"
2. If updating: previous ingredients shown, user can delete items before adding
3. App prompts: "Tell me what's in your fridge"
4. User speaks naturally while looking through their fridge
5. Items appear on screen in real-time as system recognizes them
6. User taps any misheard items to correct inline
7. User says "done" or "that's it" when finished
8. Final list displayed with "Looks good, plan my meals!" button
9. User reviews, makes final edits, then proceeds to meal planning

## Input Methods

Priority order:

1. **Voice** (primary): Continuous listening with smart pause detection
2. **Text** (fallback): Same parsing backend, accessible via "type instead" option
3. **Photo** (future): Hooks in place for image recognition integration

## Key UX Principles

- Hands-free operation while user is at their fridge
- Real-time feedback builds confidence
- Explicit user control at transition points

## Data Model

### Ingredient

```typescript
interface Ingredient {
  id: string;
  name: string;           // "chicken breast", "cherry tomatoes"
  quantity: string;       // "2", "half", "some", "a couple"
  unit?: string;          // "pieces", "head", "bag" (when detectable)
  raw_input: string;      // Original user phrase for debugging
  confidence: number;     // 0-1 parsing confidence score
  created_at: timestamp;
}
```

### Ingredient Session

```typescript
interface IngredientSession {
  id: string;
  user_id: string;
  ingredients: Ingredient[];
  created_at: timestamp;
  updated_at: timestamp;
  status: "in_progress" | "confirmed" | "used";
}
```

## Parsing Pipeline

1. Voice audio → Web Speech API transcription → raw text stream
2. Raw text accumulated until pause detected or wake word heard
3. Text sent to OpenAI Structured Outputs with schema:
   - Extract individual ingredients
   - Parse approximate quantities
   - Preserve ingredient specificity (cherry tomatoes ≠ tomatoes)
   - Return confidence scores
4. Low-confidence items flagged visually for user attention

## Assumed Pantry Staples

Excluded from input requirements and shopping lists:

- Salt, pepper, cooking oil, butter
- Sugar, flour (basic baking)
- Common dried herbs/spices

## Frontend Components

```
IngredientCollectionPage
├── SessionStartModal        // "Start fresh" vs "Update last list"
├── VoiceInputController     // Manages microphone, Web Speech API
│   ├── MicrophoneButton     // Visual state indicator (listening/paused)
│   └── AudioVisualizer      // Waveform feedback while speaking
├── IngredientList           // Real-time display of captured items
│   └── IngredientItem       // Editable item with tap-to-fix, delete
├── TextInputFallback        // "Type instead" expandable input
└── ConfirmationFooter       // "Looks good, plan my meals!" CTA
```

## Backend Endpoints (FastAPI)

### POST /api/ingredients/parse

Parse raw text into structured ingredients.

- **Input**: `{ text: string }`
- **Output**: `{ ingredients: Ingredient[], raw_input: string }`
- Calls OpenAI Structured Outputs

### POST /api/ingredients/session

Create new ingredient session for user.

### PATCH /api/ingredients/session/{id}

Update session (add/remove/edit ingredients).

### GET /api/ingredients/session/latest

Return user's most recent session (for "update last list" flow).

## LangGraph Integration

- Ingredient session feeds into the first node of the meal planning graph
- Session ID passed as input to graph execution
- Graph can query session data as needed during recipe matching

## Error Handling

### Voice Input Errors

| Scenario | Detection | User Experience |
|----------|-----------|-----------------|
| Microphone permission denied | Browser API error | Show text input immediately with "Microphone unavailable - type your ingredients" |
| No speech detected (silence) | 30s timeout | Gentle prompt: "I didn't catch anything. Tap the mic to try again or type instead" |
| Poor transcription quality | Low confidence score from Speech API | Highlight uncertain items in yellow, prompt user to verify |
| Background noise interference | Multiple low-confidence results | "Having trouble hearing clearly. Try moving somewhere quieter or type instead" |

### Parsing Errors

| Scenario | Detection | User Experience |
|----------|-----------|-----------------|
| OpenAI API failure | HTTP error / timeout | "Couldn't process that - trying again..." (auto-retry 2x, then fallback to raw text display for manual edit) |
| Unparseable input | Empty ingredients array returned | Show raw text, ask "I didn't recognize any ingredients. Could you rephrase?" |
| Ambiguous item | Low confidence on specific item | Show item with "?" icon, tap to clarify or edit |

### Network Errors

- **Offline detection**: Show banner "You're offline - voice input unavailable" and enable text-only mode with local storage queue
- **Session save failures**: Optimistic UI with background retry, alert only after 3 failures

## Testing Strategy

### Unit Tests

- Ingredient parser: Verify OpenAI structured output schema handles various input patterns
  - "2 chicken breasts" → {name: "chicken breast", quantity: "2"}
  - "some leftover rice" → {name: "rice", quantity: "some"}
  - "half a red onion" → {name: "red onion", quantity: "half"}
- Specificity preservation: "cherry tomatoes" stays "cherry tomatoes", not normalized to "tomatoes"
- Session management: Create, update, retrieve, handle missing sessions

### Integration Tests

- Voice → Parse → Display pipeline (mock Web Speech API)
- Session persistence: Start fresh vs. update last list flows
- API endpoints: Parse endpoint with realistic inputs, session CRUD operations
- OpenAI fallback: Verify retry logic and graceful degradation

### Frontend Component Tests

- IngredientList: Renders items, handles tap-to-edit, delete
- VoiceInputController: State transitions (idle → listening → processing)
- ConfirmationFooter: Disabled until ingredients exist, enables correctly

### E2E Tests (Playwright)

- Happy path: Grant mic permission → speak ingredients → see list → confirm → proceed
- Fallback path: Deny mic → type ingredients → confirm → proceed
- Edit flow: Add items → tap to edit one → delete another → confirm

### Manual Testing Checklist

- [ ] Test on actual mobile devices (iOS Safari, Android Chrome)
- [ ] Test in noisy environment
- [ ] Test with accented speech
- [ ] Test with slow/fast speakers

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary input | Voice with continuous listening | Hands-free while at fridge |
| Wake words | "done", "that's it" | Natural conversation endings |
| Confirmation | Real-time visual feedback | Builds confidence without interrupting flow |
| Detail level | Items + approximate quantities | Enough for smart matching, not tedious inventory |
| Normalization | Preserve specificity | "cherry tomatoes" ≠ "tomatoes" for accurate matching |
| Parsing | OpenAI Structured Outputs | Handles natural language complexity, consistent with stack |
| Fallbacks | Multi-modal (voice → text → future photo) | Practical accessibility |
| Pantry staples | Assume standard pantry | Reduces friction |
| Transition | Confirmation gate | User control before AI work |
| Returning users | Manual choice | Respects different usage patterns |
| API style | REST with FastAPI | Simple data model, LangGraph integration |
