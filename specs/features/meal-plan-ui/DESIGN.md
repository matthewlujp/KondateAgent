---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#frontend-patterns
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/DOMAIN.md#mealplan
  - ../../../specs/DOMAIN.md#mealslot
  - ../../../specs/PRINCIPLES.md#mobile-first
status: implemented
---

# Design: Meal Plan UI

Technical implementation of the meal plan display and chat interface.

## Component Architecture

```
MealPlanningPage
├── CollapsibleSection              # Wrapper for each major section
│   ├── Header (click to collapse)
│   └── Content (animated show/hide)
├── IngredientSection
│   ├── VoiceInputController
│   ├── IngredientList
│   └── ConfirmationFooter
├── RecipeSection
│   ├── RecipeSearchProgress
│   └── RecipeCard[]
├── MealPlanSection
│   ├── DayToggle[]                 # Enable/disable days
│   ├── GeneratePlanButton
│   └── MealSlotCard[]
│       └── ExpandableMealCard
├── ChatFAB                         # Floating action button
└── ChatBottomSheet                 # Mobile chat overlay
    └── ChatPanel
        ├── MessageList
        └── MessageInput
```

## Key Components

### ExpandableMealCard

```typescript
interface ExpandableMealCardProps {
  slot: MealSlot;
  recipe: Recipe;
  isExpanded: boolean;
  onToggle: () => void;
}

// States:
// - Collapsed: day, title, thumbnail (64px)
// - Expanded: + cooking time, ingredients, recipe link
// - Disabled: "Skipped" badge, no expansion
```

**Animation:**
```css
.card-content {
  transition: max-height 200ms ease-out;
  overflow: hidden;
}
```

### ChatFAB

```typescript
interface ChatFABProps {
  onClick: () => void;
  isOpen: boolean;
}

// Position: fixed, bottom-right
// Size: 56x56px (touch-friendly)
// Icon: chat bubble (closed), X (open)
```

### ChatBottomSheet

```typescript
interface ChatBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  planId: string;
}

// Height: 50vh (half screen)
// Entrance: slide up from bottom
// Exit: slide down or tap outside
```

**Styles:**
```css
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50vh;
  border-radius: 16px 16px 0 0;
  transform: translateY(100%);
  transition: transform 300ms ease-out;
}

.bottom-sheet.open {
  transform: translateY(0);
}
```

### ChatPanel

```typescript
interface ChatPanelProps {
  planId: string;
  onPlanUpdate: (plan: MealPlan) => void;
}

// Message display: newest at bottom
// Input: fixed at bottom of panel
// Submit: Enter key or send button
```

## State Management

### Page State

```typescript
// MealPlanningPage.tsx
const [expandedDay, setExpandedDay] = useState<DayOfWeek | null>(null);
const [isChatOpen, setIsChatOpen] = useState(false);
const [enabledDays, setEnabledDays] = useState<DayOfWeek[]>(ALL_DAYS);
```

### Server State (TanStack Query)

```typescript
// Meal plan data
const { data: plan, refetch } = useQuery({
  queryKey: ['mealPlan', planId],
  queryFn: () => getMealPlan(planId),
  staleTime: 5 * 60 * 1000,  // 5 minutes
});

// Chat mutation
const chatMutation = useMutation({
  mutationFn: (message: string) => sendChatMessage(planId, message),
  onSuccess: (response) => {
    // Update plan in cache
    queryClient.setQueryData(['mealPlan', planId], response.plan);
  },
});
```

### Chat Messages (Local State)

```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);

// Add user message immediately (optimistic)
// Add assistant message on response
```

## Responsive Behavior

| Breakpoint | Chat Behavior | Layout |
|------------|---------------|--------|
| < 768px | Bottom sheet (50vh) | Single column |
| >= 768px | Sidebar panel | Two columns |

```typescript
const isMobile = useMediaQuery('(max-width: 767px)');

return isMobile ? (
  <ChatBottomSheet {...props} />
) : (
  <ChatSidebar {...props} />
);
```

## API Integration

### Fetch Plan with Recipes

```typescript
async function getMealPlan(planId: string): Promise<MealPlanWithRecipes> {
  const response = await client.get(`/meal-plans/${planId}`);
  return response.data;
}

interface MealPlanWithRecipes {
  plan: MealPlan;
  recipes: Recipe[];  // Keyed by recipe_id
}
```

### Send Chat Message

```typescript
async function sendChatMessage(
  planId: string,
  message: string
): Promise<ChatResponse> {
  const response = await client.post(`/meal-plans/${planId}/chat`, { message });
  return response.data;
}
```

## Styling

### Tailwind Classes

```jsx
// ExpandableMealCard collapsed
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow-sm">
  <img className="w-16 h-16 rounded object-cover" />
  <div className="flex-1">
    <span className="text-sm text-gray-500">{day}</span>
    <h3 className="font-medium">{title}</h3>
  </div>
</div>

// ChatFAB
<button className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-blue-600 text-white shadow-lg">

// ChatBottomSheet
<div className="fixed inset-x-0 bottom-0 h-[50vh] bg-white rounded-t-2xl shadow-2xl">
```

## Accessibility

- All interactive elements have `role` and `aria-*` attributes
- Keyboard navigation: Tab through cards, Enter to expand
- Screen reader: Announces expanded/collapsed state
- Focus trap in chat bottom sheet when open

## Testing

### Component Tests

```typescript
describe('ExpandableMealCard', () => {
  it('expands on click', () => {});
  it('collapses on second click', () => {});
  it('shows recipe details when expanded', () => {});
});

describe('ChatBottomSheet', () => {
  it('opens with slide animation', () => {});
  it('closes on backdrop click', () => {});
  it('sends message on submit', () => {});
});
```

### E2E Tests (Playwright)

```typescript
test('expand meal card and view details', async ({ page }) => {
  await page.click('[data-day="monday"]');
  await expect(page.locator('.ingredients-list')).toBeVisible();
});

test('open chat and refine plan', async ({ page }) => {
  await page.click('[data-testid="chat-fab"]');
  await page.fill('[data-testid="chat-input"]', 'Change Tuesday');
  await page.click('[data-testid="send-button"]');
  await expect(page.locator('.assistant-message')).toBeVisible();
});
```

## Related Documents

- Design: [Docs/plans/2026-01-29-mobile-friendly-meal-plan-ui-design.md](../../../Docs/plans/2026-01-29-mobile-friendly-meal-plan-ui-design.md)
- Implementation: [Docs/plans/2026-01-29-mobile-friendly-meal-plan-ui-implementation.md](../../../Docs/plans/2026-01-29-mobile-friendly-meal-plan-ui-implementation.md)
