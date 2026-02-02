---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/ARCHITECTURE.md#frontend-patterns
  - ../../../specs/DOMAIN.md#languagesettings
status: implemented
---

# Design: Language Settings

Technical implementation of language settings and internationalization.

## Data Models

### LanguageSettings

```python
SystemLanguage = Literal["en", "ja"]
RecipeLanguage = Literal["en", "ja"]

class LanguageSettings(BaseModel):
    system_language: SystemLanguage = "en"
    recipe_search_languages: list[RecipeLanguage] = ["en"]

    class Config:
        populate_by_name = True

    # Aliases for API camelCase compatibility
    system_language: SystemLanguage = Field(alias="systemLanguage")
    recipe_search_languages: list[RecipeLanguage] = Field(alias="recipeSearchLanguages")
```

### Frontend Types

```typescript
type SystemLanguage = 'en' | 'ja';
type RecipeLanguage = 'en' | 'ja';

interface LanguageSettings {
  systemLanguage: SystemLanguage;
  recipeSearchLanguages: RecipeLanguage[];
}

// UI constants
const SYSTEM_LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
];

const RECIPE_LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
];
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/settings/language` | GET | Get current language settings |
| `/api/settings/language` | PUT | Update language settings |

### Get Response

```json
{
  "systemLanguage": "en",
  "recipeSearchLanguages": ["en", "ja"]
}
```

### Update Request/Response

```python
# Request body = LanguageSettings
# Response = Updated LanguageSettings
```

## Backend Services

### SettingsStore

```python
class SettingsStore:
    _language_settings: Optional[LanguageSettings] = None  # In-memory (temporary)

    def get_language_settings(self, user_id: Optional[str] = None) -> LanguageSettings:
        """Return current settings or defaults."""
        return self._language_settings or LanguageSettings()

    def update_language_settings(
        self,
        settings: LanguageSettings,
        user_id: Optional[str] = None
    ) -> LanguageSettings:
        """Update and persist settings."""
        self._language_settings = settings
        return settings
```

**Note**: Currently in-memory storage. Will migrate to database when user authentication is implemented.

## Frontend Architecture

### i18n Setup

```typescript
// frontend/src/i18n/index.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslations from './locales/en.json';
import jaTranslations from './locales/ja.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      ja: { translation: jaTranslations },
    },
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });
```

### Translation Files

```
frontend/src/i18n/
├── index.ts          # i18n configuration
└── locales/
    ├── en.json       # English translations
    └── ja.json       # Japanese translations
```

Translation structure:
```json
{
  "common": { "save": "...", "cancel": "...", ... },
  "settings": { "language": "...", "displayLanguage": "...", ... },
  "mealPlanning": { "title": "...", "generatePlan": "...", ... },
  "ingredients": { "voiceInputLabel": "...", ... },
  "languages": { "en": "English", "ja": "日本語" },
  "days": { "monday": "...", ... }
}
```

### Context Provider

```typescript
// frontend/src/contexts/LanguageSettingsContext.tsx

interface LanguageSettingsContextValue {
  systemLanguage: SystemLanguage;
  recipeSearchLanguages: RecipeLanguage[];
  setSystemLanguage: (language: SystemLanguage) => Promise<void>;
  setRecipeSearchLanguages: (languages: RecipeLanguage[]) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

function LanguageSettingsProvider({ children }: { children: ReactNode }) {
  // State management with optimistic updates
  // Auto-sync: changing systemLanguage adds it to recipeSearchLanguages
  // Persistence: backend API + localStorage fallback
}

function useLanguageSettings(): LanguageSettingsContextValue {
  // Hook for consuming context
}
```

### Persistence Strategy

**Multi-layer approach:**

1. **Backend API (primary)**
   - Initial load fetches from `/api/settings/language`
   - Updates immediately persist to backend

2. **localStorage (fallback cache)**
   - Key: `'languageSettings'`
   - Updated on successful API calls
   - Used when backend unavailable

3. **Defaults (last resort)**
   - `systemLanguage: 'en'`
   - `recipeSearchLanguages: ['en']`

**Load priority**: Backend API → localStorage → Defaults

## Frontend Components

```
SettingsPage
└── LanguageSettingsSection
    ├── SystemLanguageSelector     # Radio button group
    │   └── LanguageButton[]       # en / ja buttons
    └── RecipeLanguagesSelector    # Checkbox group
        └── LanguageCheckbox[]     # en / ja checkboxes
```

### LanguageSettingsSection

```typescript
function LanguageSettingsSection() {
  const { t } = useTranslation();
  const {
    systemLanguage,
    recipeSearchLanguages,
    setSystemLanguage,
    setRecipeSearchLanguages,
    isLoading,
  } = useLanguageSettings();

  // Handle system language change
  const handleSystemLanguageChange = async (lang: SystemLanguage) => {
    await setSystemLanguage(lang);
    i18n.changeLanguage(lang);
  };

  // Handle recipe language toggle (minimum 1 required)
  const handleRecipeLanguageToggle = async (lang: RecipeLanguage) => {
    if (recipeSearchLanguages.includes(lang)) {
      if (recipeSearchLanguages.length > 1) {
        await setRecipeSearchLanguages(
          recipeSearchLanguages.filter(l => l !== lang)
        );
      } else {
        // Switch to other language
        const other = lang === 'en' ? 'ja' : 'en';
        await setRecipeSearchLanguages([other]);
      }
    } else {
      await setRecipeSearchLanguages([...recipeSearchLanguages, lang]);
    }
  };
}
```

## State Management

### Optimistic Updates

```typescript
const setSystemLanguage = async (language: SystemLanguage) => {
  const previousLanguage = systemLanguage;
  const previousRecipeLanguages = recipeSearchLanguages;

  // Optimistic update
  setStateSystemLanguage(language);

  // Auto-add to recipe languages
  if (!recipeSearchLanguages.includes(language)) {
    setStateRecipeLanguages([...recipeSearchLanguages, language]);
  }

  try {
    await persistSettings(newSettings);
  } catch (error) {
    // Rollback on failure
    setStateSystemLanguage(previousLanguage);
    setStateRecipeLanguages(previousRecipeLanguages);
    i18n.changeLanguage(previousLanguage);
  }
};
```

## Integration Points

### App Provider Hierarchy

```typescript
// App.tsx
<QueryClientProvider>
  <LanguageSettingsProvider>
    <BrowserRouter>
      <Routes />
    </BrowserRouter>
  </LanguageSettingsProvider>
</QueryClientProvider>
```

### i18n Initialization

```typescript
// main.tsx
import './i18n';  // Initialize before React renders
```

### Recipe Search Integration

Recipe search services use `recipeSearchLanguages` to filter results:

```python
async def search_recipes(user_id: str, ingredients: list[str]):
    settings = settings_store.get_language_settings(user_id)
    languages = settings.recipe_search_languages

    # Filter YouTube searches by language
    # Filter Instagram searches by language
```

## Error Handling

| Error | Detection | UI Response |
|-------|-----------|-------------|
| Backend unavailable | Fetch failure | Use cached settings |
| Update failed | API error | Rollback + error state |
| No cache available | localStorage empty | Use defaults |

## Testing

### Unit Tests
- LanguageSettings model validation
- Settings store CRUD operations
- Translation key completeness

### Integration Tests
- GET/PUT settings flow
- Persistence across page refresh
- Fallback behavior

### Frontend Tests
- LanguageSettingsSection rendering
- Language switch updates i18n
- Checkbox minimum-one validation
- Optimistic update + rollback

## Related Documents

- Translation files: `frontend/src/i18n/locales/`
- Settings API: `backend/app/routers/settings.py`
- Context provider: `frontend/src/contexts/LanguageSettingsContext.tsx`
