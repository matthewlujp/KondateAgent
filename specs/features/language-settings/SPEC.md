# Feature: Language Settings

## Purpose

Let users configure their preferred language for the application UI and specify which language recipes they want to search for.

## User Problem

Users speak different languages and want:
- An interface in their native language
- Recipes from creators who speak languages they understand
- Flexibility to search multiple language sources (e.g., both English and Japanese cooking channels)

## Behavior

### Two Language Settings

1. **System Language**: Controls the application UI language
   - Single selection
   - Changes all labels, buttons, messages immediately
   - Default: English

2. **Recipe Search Languages**: Controls which language recipes to find
   - Multiple selection (at least one required)
   - Affects YouTube channel/video filtering
   - Default: Same as system language

### Supported Languages

- **English (en)**: Default
- **Japanese (ja)**: 日本語

### How to Change

1. Go to Settings
2. Find "Language" section
3. Tap desired display language (radio button style)
4. Check/uncheck recipe language boxes
5. Changes save automatically

### Auto-Sync Behavior

When changing system language:
- System language is automatically added to recipe search languages
- Ensures users can always find recipes in their display language

### Persistence

- Settings persist across page refreshes
- Settings persist across browser sessions
- Falls back gracefully if backend unavailable

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| Try to uncheck last recipe language | Switches to other language instead |
| Backend unavailable | Uses cached settings from localStorage |
| No cached settings | Uses English defaults |
| Language change fails | Rolls back to previous settings |

## Success Criteria

- Language switch is immediate (no page reload)
- All UI text updates instantly when changing system language
- Recipe search respects language filter settings
- Settings persist reliably
