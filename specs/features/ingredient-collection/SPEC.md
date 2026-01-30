# Feature: Ingredient Collection

## Purpose

Enable users to quickly tell the app what ingredients they have, without tedious typing or scrolling through lists.

## User Problem

Users stand in front of their fridge wondering "what can I make?" They need a fast way to communicate what's available without interrupting their flow.

## Behavior

### Starting a Session

- **New users**: App prompts "Tell me what's in your fridge"
- **Returning users**: Choice between "Start fresh" or "Update last list"

### Adding Ingredients

1. User speaks naturally: "I have chicken breast, some tomatoes, half an onion, and pasta"
2. Items appear on screen in real-time as recognized
3. User continues adding while looking through fridge
4. Say "done" or tap button when finished

### Editing

- Tap any item to edit if misheard
- Swipe or tap X to delete items
- Type instead of speaking if preferred

### Confirmation

- Final list displayed with all ingredients
- "Looks good, plan my meals!" button to proceed
- User can still edit before confirming

## Input Methods

| Method | When to Use |
|--------|-------------|
| Voice (primary) | Hands-free while at fridge |
| Text (fallback) | Quiet environments, preference |
| Photo (future) | Quick capture of fridge contents |

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| Microphone denied | Show text input immediately |
| Unclear speech | Highlight uncertain items for review |
| No ingredients detected | Prompt to rephrase or type |
| User says ambiguous quantity ("some", "a bit") | Accept as-is, don't force precision |

## Success Criteria

- User can input 10+ ingredients in under 60 seconds
- Minimal corrections needed for clear speech
- Works one-handed while holding fridge door
