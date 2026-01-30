# Mobile-Friendly Meal Plan UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the meal planning UI into a single mobile-friendly page with collapsible sections, expandable meal cards, and a floating chat interface.

**Architecture:** Consolidate `IngredientCollectionPage` and `MealPlanPage` into a single unified page with three collapsible sections (Ingredients, Recipes, Meal Plan). Replace the side-by-side grid layout with a vertical expandable card list. Convert the chat panel into a floating action button (FAB) that opens a bottom sheet on mobile or sidebar on desktop.

**Tech Stack:** React, TypeScript, Tailwind CSS, React Router, Vite, Vitest

---

## Task 1: Create CollapsibleSection Component

**Files:**
- Create: `frontend/src/components/CollapsibleSection.tsx`
- Create: `frontend/test/components/CollapsibleSection.test.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write the failing test**

Create `frontend/test/components/CollapsibleSection.test.tsx`:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CollapsibleSection } from '../../src/components/CollapsibleSection';

describe('CollapsibleSection', () => {
  it('renders with title and content expanded by default', () => {
    render(
      <CollapsibleSection title="Test Section">
        <div>Test Content</div>
      </CollapsibleSection>
    );

    expect(screen.getByText('Test Section')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('collapses and expands when header is clicked', async () => {
    const user = userEvent.setup();
    render(
      <CollapsibleSection title="Test Section">
        <div>Test Content</div>
      </CollapsibleSection>
    );

    const header = screen.getByRole('button', { name: /test section/i });
    const content = screen.getByText('Test Content');

    expect(content).toBeVisible();

    await user.click(header);
    expect(content).not.toBeVisible();

    await user.click(header);
    expect(content).toBeVisible();
  });

  it('starts collapsed when defaultExpanded is false', () => {
    render(
      <CollapsibleSection title="Test Section" defaultExpanded={false}>
        <div>Test Content</div>
      </CollapsibleSection>
    );

    expect(screen.getByText('Test Content')).not.toBeVisible();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- CollapsibleSection.test.tsx`
Expected: FAIL with "Cannot find module '../../src/components/CollapsibleSection'"

**Step 3: Write minimal implementation**

Create `frontend/src/components/CollapsibleSection.tsx`:

```typescript
import { useState, ReactNode } from 'react';

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  defaultExpanded?: boolean;
}

export function CollapsibleSection({
  title,
  children,
  defaultExpanded = true,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <section className="bg-white border border-sand-200 rounded-xl shadow-warm overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between bg-sand-50 hover:bg-sand-100 transition-colors"
        aria-expanded={isExpanded}
      >
        <h2 className="text-lg font-semibold text-sand-900">{title}</h2>
        <svg
          className={`w-5 h-5 text-sand-600 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && <div className="p-6">{children}</div>}
    </section>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- CollapsibleSection.test.tsx`
Expected: PASS (all tests)

**Step 5: Export component**

Modify `frontend/src/components/index.ts`:

```typescript
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
export { VoiceInputController } from './VoiceInputController';
export { TextInputFallback } from './TextInputFallback';
export { ConfirmationFooter } from './ConfirmationFooter';
export { SessionStartModal } from './SessionStartModal';
export { RecipeSearchProgress } from './RecipeSearchProgress';
export { ChannelCard } from './ChannelCard';
export { AddChannelInput } from './AddChannelInput';
export { ChannelManagementSection } from './ChannelManagementSection';
export { PlaceholderSection } from './PlaceholderSection';
export { ChannelBanner } from './ChannelBanner';
export { MealSlotCard } from './MealSlotCard';
export { ChatPanel } from './ChatPanel';
export { CollapsibleSection } from './CollapsibleSection';
```

**Step 6: Commit**

```bash
git add frontend/src/components/CollapsibleSection.tsx frontend/test/components/CollapsibleSection.test.tsx frontend/src/components/index.ts
git commit -m "feat: add CollapsibleSection component for mobile-friendly sections

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Create ExpandableMealCard Component

**Files:**
- Create: `frontend/src/components/ExpandableMealCard.tsx`
- Create: `frontend/test/components/ExpandableMealCard.test.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write the failing test**

Create `frontend/test/components/ExpandableMealCard.test.tsx`:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExpandableMealCard } from '../../src/components/ExpandableMealCard';
import type { MealSlot, Recipe } from '../../src/types';

const mockRecipe: Recipe = {
  id: 'recipe-1',
  source: 'youtube',
  source_id: 'yt123',
  url: 'https://youtube.com/watch?v=test',
  thumbnail_url: 'https://img.youtube.com/vi/test/default.jpg',
  title: 'Chicken Teriyaki Bowl',
  creator_name: 'CookingWithDog',
  creator_id: 'creator-1',
  extracted_ingredients: ['chicken breast', 'soy sauce', 'mirin', 'rice'],
  raw_description: 'Delicious teriyaki recipe',
  duration: 1800,
  posted_at: '2024-01-01T00:00:00Z',
  cache_expires_at: '2024-02-01T00:00:00Z',
};

const mockSlot: MealSlot = {
  id: 'slot-1',
  day: 'monday',
  enabled: true,
  recipe_id: 'recipe-1',
  assigned_at: '2024-01-01T00:00:00Z',
  swap_count: 0,
};

describe('ExpandableMealCard', () => {
  it('renders collapsed by default with day and recipe title', () => {
    render(<ExpandableMealCard slot={mockSlot} recipe={mockRecipe} />);

    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('Chicken Teriyaki Bowl')).toBeInTheDocument();
    expect(screen.getByText('CookingWithDog')).toBeInTheDocument();
  });

  it('expands to show details when clicked', async () => {
    const user = userEvent.setup();
    render(<ExpandableMealCard slot={mockSlot} recipe={mockRecipe} />);

    // Details should not be visible initially
    expect(screen.queryByText(/30 min/)).not.toBeInTheDocument();

    // Click to expand
    const card = screen.getByRole('button');
    await user.click(card);

    // Details should now be visible
    expect(screen.getByText(/30 min/)).toBeInTheDocument();
    expect(screen.getByText(/chicken breast/i)).toBeInTheDocument();
  });

  it('renders skipped state for disabled days', () => {
    const disabledSlot: MealSlot = {
      ...mockSlot,
      enabled: false,
      recipe_id: undefined,
    };

    render(<ExpandableMealCard slot={disabledSlot} />);

    expect(screen.getByText(/Monday/)).toBeInTheDocument();
    expect(screen.getByText(/Skipped/)).toBeInTheDocument();
  });

  it('renders empty state when no recipe assigned', () => {
    const emptySlot: MealSlot = {
      ...mockSlot,
      recipe_id: undefined,
    };

    render(<ExpandableMealCard slot={emptySlot} />);

    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText(/No recipe assigned/)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ExpandableMealCard.test.tsx`
Expected: FAIL with "Cannot find module '../../src/components/ExpandableMealCard'"

**Step 3: Write minimal implementation**

Create `frontend/src/components/ExpandableMealCard.tsx`:

```typescript
import { useState } from 'react';
import type { MealSlot, Recipe } from '../types';

interface ExpandableMealCardProps {
  slot: MealSlot;
  recipe?: Recipe;
}

/**
 * ExpandableMealCard Component
 *
 * Displays a meal slot as an expandable card.
 * - Collapsed: Shows day, thumbnail, title, creator
 * - Expanded: Shows cooking time, full ingredients, instructions preview, link
 */
export function ExpandableMealCard({ slot, recipe }: ExpandableMealCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const dayLabel = slot.day.charAt(0).toUpperCase() + slot.day.slice(1);

  // State 1: Disabled day
  if (!slot.enabled) {
    return (
      <div className="bg-sand-100 border border-sand-200 rounded-lg p-4 opacity-60 text-center">
        <div className="text-sm font-medium text-sand-600">
          {dayLabel} · Skipped
        </div>
      </div>
    );
  }

  // State 2: No recipe assigned
  if (!slot.recipe_id || !recipe) {
    return (
      <div className="bg-white border-2 border-dashed border-sand-300 rounded-lg p-4 text-center">
        <div className="text-sm font-medium text-terra-600 mb-2">
          {dayLabel}
        </div>
        <div className="text-sm text-sand-400">No recipe assigned</div>
      </div>
    );
  }

  // State 3: With recipe
  const durationMinutes = recipe.duration ? Math.round(recipe.duration / 60) : null;

  return (
    <div className="bg-white border border-sand-200 rounded-lg shadow-warm overflow-hidden">
      {/* Collapsed header - clickable */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex gap-3 items-start hover:bg-sand-50 transition-colors"
      >
        {/* Thumbnail */}
        <img
          src={recipe.thumbnail_url}
          alt={recipe.title}
          className="w-16 h-16 rounded-lg object-cover flex-shrink-0 bg-sand-100"
        />

        {/* Title and metadata */}
        <div className="flex-1 text-left min-w-0">
          <div className="text-sm font-semibold text-terra-600 mb-1">
            {dayLabel}
          </div>
          <h3 className="text-base font-semibold text-sand-900 line-clamp-2 mb-1">
            {recipe.title}
          </h3>
          <p className="text-sm text-sand-600">{recipe.creator_name}</p>
        </div>

        {/* Expand/collapse chevron */}
        <svg
          className={`w-5 h-5 text-sand-400 flex-shrink-0 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-sand-100">
          {/* Cooking time */}
          {durationMinutes && (
            <div className="flex items-center text-sm text-sand-700 pt-4">
              <svg
                className="w-4 h-4 mr-2 text-terra-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {durationMinutes} min
            </div>
          )}

          {/* Ingredients */}
          {recipe.extracted_ingredients.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-sand-900 mb-2 flex items-center">
                <svg
                  className="w-4 h-4 mr-2 text-herb-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                Ingredients
              </div>
              <ul className="space-y-1">
                {recipe.extracted_ingredients.map((ingredient, idx) => (
                  <li key={idx} className="text-sm text-sand-700 flex items-start">
                    <span className="text-terra-500 mr-2">•</span>
                    {ingredient}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Instructions preview */}
          {recipe.raw_description && (
            <div>
              <div className="text-sm font-semibold text-sand-900 mb-2 flex items-center">
                <svg
                  className="w-4 h-4 mr-2 text-terra-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Description
              </div>
              <p className="text-sm text-sand-700 line-clamp-3">
                {recipe.raw_description}
              </p>
            </div>
          )}

          {/* Link to recipe */}
          <a
            href={recipe.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm font-medium text-terra-600 hover:text-terra-700 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            View full recipe
            <svg
              className="w-4 h-4 ml-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </div>
      )}
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ExpandableMealCard.test.tsx`
Expected: PASS (all tests)

**Step 5: Export component**

Modify `frontend/src/components/index.ts`, add:

```typescript
export { ExpandableMealCard } from './ExpandableMealCard';
```

**Step 6: Commit**

```bash
git add frontend/src/components/ExpandableMealCard.tsx frontend/test/components/ExpandableMealCard.test.tsx frontend/src/components/index.ts
git commit -m "feat: add ExpandableMealCard component with independent expansion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Create ChatFAB Component

**Files:**
- Create: `frontend/src/components/ChatFAB.tsx`
- Create: `frontend/test/components/ChatFAB.test.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write the failing test**

Create `frontend/test/components/ChatFAB.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatFAB } from '../../src/components/ChatFAB';

describe('ChatFAB', () => {
  it('renders a floating button', () => {
    const mockOnClick = vi.fn();
    render(<ChatFAB onClick={mockOnClick} />);

    const button = screen.getByRole('button', { name: /chat/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const mockOnClick = vi.fn();
    render(<ChatFAB onClick={mockOnClick} />);

    const button = screen.getByRole('button', { name: /chat/i });
    await user.click(button);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('hides when isVisible is false', () => {
    const mockOnClick = vi.fn();
    render(<ChatFAB onClick={mockOnClick} isVisible={false} />);

    const button = screen.queryByRole('button', { name: /chat/i });
    expect(button).not.toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ChatFAB.test.tsx`
Expected: FAIL with "Cannot find module '../../src/components/ChatFAB'"

**Step 3: Write minimal implementation**

Create `frontend/src/components/ChatFAB.tsx`:

```typescript
interface ChatFABProps {
  onClick: () => void;
  isVisible?: boolean;
}

/**
 * ChatFAB Component
 *
 * Floating action button for opening the chat interface.
 * Fixed position at bottom-right corner.
 */
export function ChatFAB({ onClick, isVisible = true }: ChatFABProps) {
  if (!isVisible) return null;

  return (
    <button
      onClick={onClick}
      aria-label="Open chat"
      className="fixed bottom-6 right-6 w-14 h-14 bg-terra-500 text-white rounded-full shadow-lg hover:bg-terra-600 transition-colors flex items-center justify-center z-50"
    >
      <svg
        className="w-6 h-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
        />
      </svg>
    </button>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ChatFAB.test.tsx`
Expected: PASS (all tests)

**Step 5: Export component**

Modify `frontend/src/components/index.ts`, add:

```typescript
export { ChatFAB } from './ChatFAB';
```

**Step 6: Commit**

```bash
git add frontend/src/components/ChatFAB.tsx frontend/test/components/ChatFAB.test.tsx frontend/src/components/index.ts
git commit -m "feat: add ChatFAB floating action button

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Create ChatBottomSheet Component

**Files:**
- Create: `frontend/src/components/ChatBottomSheet.tsx`
- Create: `frontend/test/components/ChatBottomSheet.test.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write the failing test**

Create `frontend/test/components/ChatBottomSheet.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatBottomSheet } from '../../src/components/ChatBottomSheet';
import type { ChatMessage } from '../../src/types';

const mockMessages: ChatMessage[] = [
  {
    role: 'user',
    content: 'Change Tuesday',
    timestamp: '2024-01-01T00:00:00Z',
  },
  {
    role: 'assistant',
    content: 'I swapped Tuesday to a lighter meal.',
    timestamp: '2024-01-01T00:01:00Z',
  },
];

describe('ChatBottomSheet', () => {
  it('renders when isOpen is true', () => {
    const mockOnClose = vi.fn();
    const mockOnSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={mockOnClose}
        messages={mockMessages}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    expect(screen.getByText('Refine Your Plan')).toBeInTheDocument();
    expect(screen.getByText('Change Tuesday')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    const mockOnClose = vi.fn();
    const mockOnSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={false}
        onClose={mockOnClose}
        messages={[]}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    expect(screen.queryByText('Refine Your Plan')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    const mockOnSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={mockOnClose}
        messages={[]}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    const mockOnSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={mockOnClose}
        messages={[]}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const backdrop = screen.getByTestId('chat-backdrop');
    await user.click(backdrop);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ChatBottomSheet.test.tsx`
Expected: FAIL with "Cannot find module '../../src/components/ChatBottomSheet'"

**Step 3: Write minimal implementation**

Create `frontend/src/components/ChatBottomSheet.tsx`:

```typescript
import { useState, useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';

interface ChatBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

/**
 * ChatBottomSheet Component
 *
 * Mobile bottom sheet for chat interface.
 * Slides up from bottom with semi-transparent backdrop.
 * Closable via X button, backdrop tap, or drag down.
 */
export function ChatBottomSheet({
  isOpen,
  onClose,
  messages,
  onSendMessage,
  isLoading,
}: ChatBottomSheetProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed && !isLoading) {
      onSendMessage(trimmed);
      setInputValue('');
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        data-testid="chat-backdrop"
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div className="fixed inset-x-0 bottom-0 z-50 lg:hidden">
        <div className="bg-white rounded-t-2xl shadow-2xl max-h-[70vh] flex flex-col">
          {/* Drag handle */}
          <div className="pt-2 pb-1 flex justify-center">
            <div className="w-12 h-1 bg-sand-300 rounded-full" />
          </div>

          {/* Header */}
          <div className="px-4 py-3 border-b border-sand-200 flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-terra-700">
                Refine Your Plan
              </h3>
              <p className="text-xs text-terra-600 mt-0.5">
                Ask to swap meals or make changes
              </p>
            </div>
            <button
              onClick={onClose}
              aria-label="Close chat"
              className="p-2 text-sand-600 hover:bg-sand-100 rounded-full transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.length === 0 ? (
              // Empty state
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-12 h-12 bg-terra-100 rounded-full flex items-center justify-center mb-3">
                  <svg
                    className="w-6 h-6 text-terra-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                </div>
                <p className="text-sm text-sand-600 mb-2">Your plan is ready!</p>
                <p className="text-xs text-sand-500 max-w-xs">
                  Try: "Swap Tuesday for something lighter" or "Change Friday to a
                  vegetarian meal"
                </p>
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-4 py-2.5 ${
                        message.role === 'user'
                          ? 'bg-terra-500 text-white'
                          : 'bg-sand-100 text-sand-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {message.content}
                      </p>
                    </div>
                  </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-sand-100 rounded-lg px-4 py-3">
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                        <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                        <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce" />
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Form */}
          <div className="p-4 border-t border-sand-200 bg-sand-50">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask to swap a meal..."
                disabled={isLoading}
                className="flex-1 px-4 py-2.5 border border-sand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terra-500 disabled:bg-sand-100 disabled:text-sand-500 text-sm"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="px-5 py-2.5 bg-terra-500 text-white rounded-lg font-medium hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed text-sm"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ChatBottomSheet.test.tsx`
Expected: PASS (all tests)

**Step 5: Export component**

Modify `frontend/src/components/index.ts`, add:

```typescript
export { ChatBottomSheet } from './ChatBottomSheet';
```

**Step 6: Commit**

```bash
git add frontend/src/components/ChatBottomSheet.tsx frontend/test/components/ChatBottomSheet.test.tsx frontend/src/components/index.ts
git commit -m "feat: add ChatBottomSheet mobile chat interface

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Create Unified MealPlanningPage

**Files:**
- Create: `frontend/src/pages/MealPlanningPage.tsx`
- Modify: `frontend/src/pages/index.ts`

**Step 1: Create the unified page**

Create `frontend/src/pages/MealPlanningPage.tsx`:

```typescript
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  SessionStartModal,
  VoiceInputController,
  TextInputFallback,
  IngredientList,
  RecipeSearchProgress,
  ChannelBanner,
  CollapsibleSection,
  ExpandableMealCard,
  ChatFAB,
  ChatBottomSheet,
  ChatPanel,
} from '../components';
import {
  authApi,
  ingredientsApi,
  streamRecipeSearch,
  tokenManager,
  creatorsApi,
  mealPlansApi,
} from '../api';
import type {
  Ingredient,
  IngredientSession,
  ProgressEvent,
  ScoredRecipe,
  DayOfWeek,
  MealPlan,
  ChatMessage,
} from '../types';
import { ALL_DAYS } from '../types';

const USER_ID = 'demo-user';

const WEEKDAY_DEFAULTS: DayOfWeek[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
];

/**
 * MealPlanningPage Component
 *
 * Unified page for the entire meal planning workflow:
 * 1. Ingredient collection
 * 2. Recipe search
 * 3. Meal plan generation and refinement
 *
 * Each section is collapsible and has independent refresh buttons.
 */
export function MealPlanningPage() {
  // Session state
  const [session, setSession] = useState<IngredientSession | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [existingSession, setExistingSession] = useState<IngredientSession | null>(
    null
  );

  // UI state
  const [isTextInputExpanded, setIsTextInputExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Recipe search state
  const [isSearching, setIsSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState<ProgressEvent | null>(null);
  const [searchComplete, setSearchComplete] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [recipes, setRecipes] = useState<ScoredRecipe[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Meal plan state
  const [enabledDays, setEnabledDays] = useState<Set<DayOfWeek>>(
    new Set(WEEKDAY_DEFAULTS)
  );
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Channel banner state
  const [bannerDismissed, setBannerDismissed] = useState(() =>
    localStorage.getItem('channelBannerDismissed') === 'true'
  );

  const { data: creators = [] } = useQuery({
    queryKey: ['creators'],
    queryFn: creatorsApi.getCreators,
    enabled: !bannerDismissed,
  });

  const showBanner = !bannerDismissed && creators.length === 0;

  const handleDismissBanner = () => {
    localStorage.setItem('channelBannerDismissed', 'true');
    setBannerDismissed(true);
  };

  // Initialize auth token and check for existing session on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  // Cleanup: abort streaming on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const initializeAuth = async (retryCount = 0) => {
    try {
      await ensureValidToken();
      await checkExistingSession();
    } catch (err: any) {
      console.error('Failed to initialize auth:', err);

      if (err.response?.status === 401 && retryCount === 0) {
        console.log('Token invalid, getting fresh token and retrying...');
        tokenManager.clearToken();
        return initializeAuth(1);
      }

      setError('Failed to authenticate. Please refresh and try again.');
    }
  };

  const ensureValidToken = async () => {
    const existingToken = tokenManager.getToken();
    if (!existingToken) {
      const tokenResponse = await authApi.getToken(USER_ID);
      tokenManager.setToken(tokenResponse.access_token);
    }
  };

  const checkExistingSession = async () => {
    try {
      const latest = await ingredientsApi.getLatestSession(USER_ID);
      if (latest && latest.status === 'in_progress') {
        setExistingSession(latest);
        setShowModal(true);
      } else {
        await createNewSession();
      }
    } catch (err: any) {
      console.error('Failed to check existing session:', err);

      if (err.response?.status === 401) {
        throw err;
      }

      await createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await ingredientsApi.createSession(USER_ID);
      setSession(newSession);
    } catch (err: any) {
      console.error('Failed to create session:', err);

      if (err.response?.status === 401) {
        throw err;
      }

      setError('Failed to start session. Please refresh and try again.');
    }
  };

  const handleUpdateExisting = () => {
    setSession(existingSession);
    setShowModal(false);
    setExistingSession(null);
  };

  const handleStartFresh = async () => {
    setShowModal(false);
    setExistingSession(null);
    await createNewSession();
  };

  const handleTextInput = async (text: string) => {
    if (!session) {
      setError('No active session. Please refresh the page.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const parseResult = await ingredientsApi.parse(text);
      const updatedSession = await ingredientsApi.addIngredients(
        session.id,
        parseResult.ingredients
      );

      setSession(updatedSession);
    } catch (err) {
      console.error('Failed to parse and add ingredients:', err);
      setError('Failed to process ingredients. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceTranscript = async (transcript: string) => {
    await handleTextInput(transcript);
  };

  const handleWakeWord = () => {
    console.log('Wake word detected');
  };

  const handleUpdateIngredient = async (
    id: string,
    updates: Partial<Ingredient>
  ) => {
    if (!session) return;

    const updatedIngredients = session.ingredients.map((ing) =>
      ing.id === id ? { ...ing, ...updates } : ing
    );
    setSession({ ...session, ingredients: updatedIngredients });
  };

  const handleDeleteIngredient = async (id: string) => {
    if (!session) return;

    setIsProcessing(true);
    setError(null);

    try {
      const updatedSession = await ingredientsApi.removeIngredient(session.id, id);
      setSession(updatedSession);
    } catch (err) {
      console.error('Failed to delete ingredient:', err);
      setError('Failed to delete ingredient. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearchRecipes = async () => {
    if (!session || session.ingredients.length === 0) {
      setError('Please add ingredients first');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      await ingredientsApi.updateStatus(session.id, 'confirmed');
      setIsProcessing(false);

      setSearchProgress(null);
      setSearchComplete(false);
      setSearchError(null);
      setRecipes([]);
      setIsSearching(true);

      const ingredientNames = session.ingredients.map((ing) => ing.name);

      const controller = await streamRecipeSearch({
        ingredients: ingredientNames,
        maxResults: 15,
        onProgress: (progress) => {
          setSearchProgress(progress);
        },
        onResult: (foundRecipes) => {
          setRecipes(foundRecipes);
          setSearchComplete(true);
          setIsSearching(false);
          console.log('Recipe search complete:', foundRecipes);
        },
        onError: (errorMessage) => {
          setSearchError(errorMessage);
          setIsSearching(false);
        },
      });

      abortControllerRef.current = controller;
    } catch (err) {
      console.error('Failed to search recipes:', err);
      setError('Failed to search recipes. Please try again.');
      setIsProcessing(false);
      setIsSearching(false);
    }
  };

  const toggleDay = (day: DayOfWeek) => {
    setEnabledDays((prev) => {
      const next = new Set(prev);
      if (next.has(day)) {
        next.delete(day);
      } else {
        next.add(day);
      }
      return next;
    });
  };

  const handleGeneratePlan = async () => {
    if (!session) {
      setError('No session found');
      return;
    }

    if (recipes.length === 0) {
      setError('No recipes found. Please search for recipes first.');
      return;
    }

    if (enabledDays.size === 0) {
      setError('Please select at least one day');
      return;
    }

    setIsGeneratingPlan(true);
    setError(null);

    try {
      const recipeIds = recipes.map((sr) => sr.recipe.id);
      const generatedPlan = await mealPlansApi.generatePlan({
        ingredient_session_id: session.id,
        enabled_days: Array.from(enabledDays),
        recipe_ids: recipeIds,
      });

      setPlan(generatedPlan);
      setChatMessages([]);
    } catch (err) {
      console.error('Failed to generate plan:', err);
      setError('Failed to generate meal plan. Please try again.');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleSendChatMessage = async (message: string) => {
    if (!plan) return;

    setIsChatLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    try {
      const response = await mealPlansApi.sendChatMessage(plan.id, message);

      setPlan(response.plan);

      if (response.recipes && response.recipes.length > 0) {
        setRecipes((prev) => {
          const existingIds = new Set(prev.map((sr) => sr.recipe.id));
          const newRecipes = response.recipes.filter(
            (r) => !existingIds.has(r.id)
          );
          const newScoredRecipes = newRecipes.map((recipe) => ({
            recipe,
            coverage_score: 1.0,
            missing_ingredients: [],
            reasoning: 'Selected via chat refinement',
          }));
          return [...prev, ...newScoredRecipes];
        });
      }

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        tool_calls:
          response.tool_calls.length > 0 ? response.tool_calls : undefined,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to send chat message:', err);
      setError('Failed to process your request. Please try again.');
      setChatMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsChatLoading(false);
    }
  };

  // Build recipe lookup map
  const recipeMap = new Map(recipes.map((sr) => [sr.recipe.id, sr.recipe]));

  return (
    <div className="min-h-screen bg-cream bg-kitchen-pattern pb-32">
      {/* Header */}
      <header className="bg-header-gradient shadow-warm-md sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white font-display">
              Plan Your Meals
            </h1>
            <p className="text-sm text-terra-50 mt-1">
              From ingredients to weekly plan
            </p>
          </div>
          <Link
            to="/settings"
            className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            aria-label="Settings"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </Link>
        </div>
      </header>

      {/* Session Start Modal */}
      <SessionStartModal
        isOpen={showModal}
        ingredientCount={existingSession?.ingredients.length || 0}
        lastUpdated={existingSession?.updated_at || ''}
        onUpdateExisting={handleUpdateExisting}
        onStartFresh={handleStartFresh}
      />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Error Display */}
        {error && (
          <div className="bg-chili-50 border-2 border-chili-300 rounded-lg p-4">
            <p className="text-sm text-chili-800">{error}</p>
          </div>
        )}

        {/* Channel Banner */}
        {showBanner && <ChannelBanner onDismiss={handleDismissBanner} />}

        {/* Section 1: Ingredients */}
        <CollapsibleSection title="§ Ingredients" defaultExpanded={true}>
          <div className="space-y-6">
            {/* Voice Input */}
            <div>
              <h3 className="text-sm font-semibold text-sand-900 mb-3 text-center">
                Add Ingredients
              </h3>
              <VoiceInputController
                onTranscript={handleVoiceTranscript}
                onWakeWord={handleWakeWord}
              />
            </div>

            {/* Text Input Fallback */}
            <TextInputFallback
              onSubmit={handleTextInput}
              isExpanded={isTextInputExpanded}
              onToggle={() => setIsTextInputExpanded(!isTextInputExpanded)}
            />

            {/* Ingredients List */}
            <div>
              <h3 className="text-sm font-semibold text-sand-900 mb-3">
                Your Ingredients
              </h3>
              <IngredientList
                ingredients={session?.ingredients || []}
                onUpdate={handleUpdateIngredient}
                onDelete={handleDeleteIngredient}
              />
            </div>

            {/* Re-search Button */}
            <button
              onClick={handleSearchRecipes}
              disabled={
                isSearching ||
                !session ||
                session.ingredients.length === 0 ||
                isProcessing
              }
              className="w-full px-6 py-3 bg-terra-500 text-white rounded-lg font-semibold hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSearching ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Searching recipes...
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Re-search Recipes
                </>
              )}
            </button>
          </div>
        </CollapsibleSection>

        {/* Recipe Search Progress */}
        {(isSearching || searchComplete || searchError) && (
          <RecipeSearchProgress
            currentProgress={searchProgress}
            isComplete={searchComplete}
            error={searchError}
          />
        )}

        {/* Section 2: Recipes */}
        {recipes.length > 0 && (
          <CollapsibleSection
            title={`§ Recipes Found (${recipes.length})`}
            defaultExpanded={true}
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {recipes.map((sr) => (
                  <div
                    key={sr.recipe.id}
                    className="bg-white border border-sand-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                  >
                    <div className="flex gap-3">
                      {sr.recipe.thumbnail_url && (
                        <img
                          src={sr.recipe.thumbnail_url}
                          alt={sr.recipe.title}
                          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <a
                          href={sr.recipe.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-terra-700 hover:underline line-clamp-2 block mb-1"
                        >
                          {sr.recipe.title}
                        </a>
                        <p className="text-xs text-sand-600">
                          {sr.recipe.creator_name} ·{' '}
                          {Math.round(sr.coverage_score * 100)}% match
                        </p>
                        {sr.missing_ingredients.length > 0 && (
                          <p className="text-xs text-chili-600 mt-1">
                            Need: {sr.missing_ingredients.slice(0, 2).join(', ')}
                            {sr.missing_ingredients.length > 2 &&
                              ` +${sr.missing_ingredients.length - 2}`}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Search Again Button */}
              <button
                onClick={handleSearchRecipes}
                disabled={isSearching || !session}
                className="w-full px-6 py-3 bg-white border-2 border-terra-500 text-terra-700 rounded-lg font-semibold hover:bg-terra-50 transition-colors disabled:bg-sand-100 disabled:border-sand-300 disabled:text-sand-500 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Search Again
              </button>
            </div>
          </CollapsibleSection>
        )}

        {/* Section 3: Meal Plan */}
        {recipes.length > 0 && (
          <CollapsibleSection title="§ Your Meal Plan" defaultExpanded={true}>
            <div className="space-y-6">
              {/* Day Toggles */}
              <div>
                <h3 className="text-sm font-semibold text-sand-900 mb-3">
                  Which days would you like to plan?
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
                  {ALL_DAYS.map((day) => {
                    const isEnabled = enabledDays.has(day);
                    const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);

                    return (
                      <button
                        key={day}
                        onClick={() => toggleDay(day)}
                        className={`p-3 rounded-lg border-2 transition-all text-sm font-medium ${
                          isEnabled
                            ? 'border-terra-500 bg-terra-50 text-terra-700'
                            : 'border-sand-200 bg-white text-sand-500 hover:border-sand-300'
                        }`}
                      >
                        {dayLabel}
                        {isEnabled && (
                          <svg
                            className="w-4 h-4 mx-auto mt-1 text-terra-500"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Meal Cards */}
              {plan && (
                <div className="space-y-3">
                  {plan.slots
                    .sort((a, b) => {
                      const dayOrder = {
                        monday: 0,
                        tuesday: 1,
                        wednesday: 2,
                        thursday: 3,
                        friday: 4,
                        saturday: 5,
                        sunday: 6,
                      };
                      return dayOrder[a.day] - dayOrder[b.day];
                    })
                    .map((slot) => (
                      <ExpandableMealCard
                        key={slot.id}
                        slot={slot}
                        recipe={
                          slot.recipe_id ? recipeMap.get(slot.recipe_id) : undefined
                        }
                      />
                    ))}
                </div>
              )}

              {/* Generate/Regenerate Plan Button */}
              <button
                onClick={handleGeneratePlan}
                disabled={
                  isGeneratingPlan || enabledDays.size === 0 || recipes.length === 0
                }
                className="w-full px-6 py-3 bg-terra-500 text-white rounded-lg font-semibold hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isGeneratingPlan ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Generating plan...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    {plan ? 'Regenerate Plan' : 'Generate Plan'}
                  </>
                )}
              </button>
            </div>
          </CollapsibleSection>
        )}
      </main>

      {/* Chat FAB - only show when plan exists */}
      {plan && (
        <>
          <ChatFAB onClick={() => setIsChatOpen(true)} isVisible={!isChatOpen} />

          {/* Mobile: Bottom Sheet */}
          <ChatBottomSheet
            isOpen={isChatOpen}
            onClose={() => setIsChatOpen(false)}
            messages={chatMessages}
            onSendMessage={handleSendChatMessage}
            isLoading={isChatLoading}
          />

          {/* Desktop: Sidebar (hidden on mobile via lg: classes) */}
          <div
            className={`hidden lg:block fixed top-0 right-0 h-screen w-80 bg-white border-l border-sand-200 shadow-2xl transition-transform z-40 ${
              isChatOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
          >
            <ChatPanel
              messages={chatMessages}
              onSendMessage={handleSendChatMessage}
              isLoading={isChatLoading}
            />
            <button
              onClick={() => setIsChatOpen(false)}
              className="absolute top-4 right-4 p-2 text-sand-600 hover:bg-sand-100 rounded-full transition-colors"
              aria-label="Close chat"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

**Step 2: Export the page**

Modify `frontend/src/pages/index.ts`:

```typescript
export { IngredientCollectionPage } from './IngredientCollectionPage';
export { SettingsPage } from './SettingsPage';
export { MealPlanPage } from './MealPlanPage';
export { MealPlanningPage } from './MealPlanningPage';
```

**Step 3: Commit**

```bash
git add frontend/src/pages/MealPlanningPage.tsx frontend/src/pages/index.ts
git commit -m "feat: add unified MealPlanningPage with collapsible sections

Consolidates ingredient collection, recipe search, and meal planning
into a single scrollable page with independent section refresh.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Update App Routing

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Update routes to use unified page**

Modify `frontend/src/App.tsx`:

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MealPlanningPage, SettingsPage } from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MealPlanningPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          {/* Redirect old routes to new unified page */}
          <Route path="/meal-plan" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

**Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: update routing to use unified MealPlanningPage

Redirects /meal-plan to / (unified page).

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Run Tests and Verify

**Files:**
- N/A (verification step)

**Step 1: Run all frontend tests**

Run: `cd frontend && npm test`
Expected: All tests pass (CollapsibleSection, ExpandableMealCard, ChatFAB, ChatBottomSheet)

**Step 2: Start dev server and manual test**

Run: `cd frontend && npm run dev`

Manual verification checklist:
- [ ] Ingredients section: Add/remove ingredients
- [ ] Click "Re-search Recipes" triggers search
- [ ] Recipes section appears with results
- [ ] Click "Search Again" refreshes recipes
- [ ] Meal Plan section: Toggle days, generate plan
- [ ] Expandable meal cards: Click to expand/collapse
- [ ] Multiple cards can be open simultaneously
- [ ] Chat FAB appears after plan is generated
- [ ] Chat FAB opens bottom sheet on mobile (resize browser < 768px)
- [ ] Chat input sends message and updates plan
- [ ] Desktop (>= 1024px): Chat opens as sidebar

**Step 3: Fix any issues found**

If issues are found during manual testing, create fixes and commit each separately.

**Step 4: Final commit**

If all tests pass and manual verification is successful:

```bash
git commit --allow-empty -m "test: verify mobile-friendly UI works end-to-end

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `README.md`

**Step 1: Update README with new page structure**

Modify `README.md` to reflect the unified page structure:

Find the section about "User Flow" or "Pages" and update:

```markdown
## User Flow

The app uses a single-page workflow for meal planning:

1. **Ingredients Section**
   - Voice or text input to add ingredients
   - Edit or remove ingredients
   - "Re-search Recipes" button triggers recipe search

2. **Recipes Section** (appears after search)
   - Displays 10-15 scored recipes
   - Shows coverage score and missing ingredients
   - "Search Again" button to refresh

3. **Meal Plan Section** (appears after recipe search)
   - Select days to plan meals for
   - "Generate Plan" creates optimized weekly plan
   - Expandable meal cards show cooking time, ingredients, instructions
   - "Regenerate Plan" creates new plan from current recipes

4. **Chat Refinement** (after plan is generated)
   - Floating action button (FAB) opens chat interface
   - Mobile: Bottom sheet popup
   - Desktop: Collapsible sidebar
   - Natural language meal swaps: "Change Tuesday to something lighter"

Each section is collapsible and has independent refresh functionality.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with unified page structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Cleanup - Remove Old MealPlanPage (Optional)

**Files:**
- Delete: `frontend/src/pages/MealPlanPage.tsx`
- Modify: `frontend/src/pages/index.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Remove MealPlanPage export**

Modify `frontend/src/pages/index.ts`:

```typescript
export { IngredientCollectionPage } from './IngredientCollectionPage';
export { SettingsPage } from './SettingsPage';
export { MealPlanningPage } from './MealPlanningPage';
```

**Step 2: Delete old file**

Run: `rm frontend/src/pages/MealPlanPage.tsx`

**Step 3: Verify no imports reference MealPlanPage**

Run: `cd frontend && grep -r "MealPlanPage" src/`
Expected: No results (or only in comments)

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove deprecated MealPlanPage

Functionality fully replaced by MealPlanningPage.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary

This implementation plan refactors the meal planning UI into a mobile-friendly single-page experience:

1. **New Components**: CollapsibleSection, ExpandableMealCard, ChatFAB, ChatBottomSheet
2. **Unified Page**: MealPlanningPage consolidates entire workflow
3. **Responsive Design**: Bottom sheet (mobile), sidebar (desktop)
4. **Independent Sections**: Each section has its own refresh button
5. **Tests**: Unit tests for all new components

**Execution Options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks
2. **Parallel Session (separate)** - Open new session with executing-plans for batch execution

Which approach would you like to use?
