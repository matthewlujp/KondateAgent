---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/ARCHITECTURE.md#backend-patterns
  - ../../../specs/DOMAIN.md#ingredient
  - ../../../specs/DOMAIN.md#ingredientsession
status: implemented
---

# Design: Ingredient Collection

Technical implementation of the ingredient collection feature.

## Data Models

### Ingredient

```python
class Ingredient(BaseModel):
    id: str                    # UUID
    name: str                  # Normalized: "chicken breast"
    quantity: str              # "2", "half", "some"
    unit: Optional[str]        # "pieces", "head", "bag"
    raw_input: str             # Original: "2 chicken breasts"
    confidence: float          # 0-1 parsing confidence
    created_at: datetime
```

### IngredientSession

```python
class IngredientSession(BaseModel):
    id: str
    user_id: str
    ingredients: list[Ingredient]
    status: Literal["in_progress", "confirmed", "used"]
    created_at: datetime
    updated_at: datetime
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ingredients/parse` | POST | Parse text → ingredients |
| `/api/ingredients/session` | POST | Create new session |
| `/api/ingredients/session/{id}` | PATCH | Update session |
| `/api/ingredients/session/{id}/confirm` | POST | Confirm session |
| `/api/ingredients/session/latest` | GET | Get most recent |

### Parse Request/Response

```python
# Request
class ParseRequest(BaseModel):
    text: str

# Response
class ParseResponse(BaseModel):
    ingredients: list[Ingredient]
    raw_input: str
```

## Parsing Pipeline

1. **Voice capture**: Web Speech API → raw text stream
2. **Pause detection**: Accumulate until silence or wake word
3. **LLM parsing**: OpenAI Structured Outputs
4. **Validation**: Confidence scoring, normalization

### OpenAI Prompt

```
Extract ingredients from natural speech. For each:
- name: normalized ingredient name (preserve specificity)
- quantity: approximate amount as spoken
- unit: if detectable
- confidence: 0-1 parsing certainty

Keep "cherry tomatoes" as-is, don't normalize to "tomatoes".
```

## Frontend Components

```
IngredientCollectionPage
├── SessionStartModal        # "Start fresh" vs "Update last"
├── VoiceInputController     # Web Speech API management
│   ├── MicrophoneButton     # State indicator
│   └── AudioVisualizer      # Waveform feedback
├── IngredientList           # Real-time display
│   └── IngredientItem       # Editable + deletable
├── TextInputFallback        # Type instead option
└── ConfirmationFooter       # "Plan my meals" CTA
```

### VoiceInputController States

```
idle → listening → processing → idle
         ↓
      error (mic denied, timeout)
```

## Backend Services

```python
class IngredientParser:
    async def parse(self, text: str) -> list[Ingredient]:
        # OpenAI structured output call
        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[...],
            response_format=IngredientList,
        )
        return response.choices[0].message.parsed.ingredients

class SessionStore:
    _sessions: dict[str, IngredientSession] = {}

    def create(self, user_id: str) -> IngredientSession: ...
    def get(self, session_id: str) -> IngredientSession: ...
    def update(self, session_id: str, ingredients: list) -> IngredientSession: ...
    def get_latest(self, user_id: str) -> Optional[IngredientSession]: ...
```

## Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Mic permission denied | Browser API error | Show text input |
| No speech (30s) | Timeout | Prompt retry or type |
| OpenAI failure | HTTP error | Retry 2x, show raw text |
| Low confidence | `< 0.7` | Highlight for user review |

## Testing

### Unit Tests
- Parser: various input patterns → correct ingredients
- Specificity: "cherry tomatoes" preserved
- Session: CRUD operations

### Integration Tests
- Voice → parse → display pipeline (mock Speech API)
- Session persistence across requests
- OpenAI retry logic

### E2E Tests (Playwright)
- Happy path: mic → speak → list → confirm
- Fallback: deny mic → type → confirm

## Related Documents

- Original design: [Docs/plans/2026-01-25-ingredient-collection-design.md](../../../Docs/plans/2026-01-25-ingredient-collection-design.md)
- Implementation: [Docs/plans/2026-01-26-ingredient-collection-implementation.md](../../../Docs/plans/2026-01-26-ingredient-collection-implementation.md)
