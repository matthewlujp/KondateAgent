import { useState } from 'react';
import type { KeyboardEvent } from 'react';

interface TextInputFallbackProps {
  onSubmit: (text: string) => void;
  isExpanded: boolean;
  onToggle: () => void;
}

/**
 * TextInputFallback Component
 *
 * Expandable text input as fallback for voice input.
 * Shows "Type instead" button that expands to reveal textarea.
 *
 * Features:
 * - Collapsible text input area
 * - Multi-line textarea for longer input
 * - Submit button with keyboard shortcut (Cmd/Ctrl+Enter)
 * - Clear button to reset input
 */
export function TextInputFallback({ onSubmit, isExpanded, onToggle }: TextInputFallbackProps) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (text.trim()) {
      onSubmit(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setText('');
  };

  if (!isExpanded) {
    return (
      <div className="text-center">
        <button
          onClick={onToggle}
          className="text-terra-600 hover:text-terra-700 font-medium text-sm underline"
        >
          Type instead
        </button>
      </div>
    );
  }

  return (
    <div className="border-2 border-sand-300 rounded-lg p-4 bg-white/80 backdrop-blur-sm animate-scale-in">
      <div className="flex items-center justify-between mb-2">
        <label htmlFor="text-input" className="text-sm font-medium text-sand-700">
          Type your ingredients
        </label>
        <button
          onClick={onToggle}
          className="text-sand-500 hover:text-sand-700"
          aria-label="Close text input"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
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

      <textarea
        id="text-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="e.g., 2 chicken breasts, 1 onion, 3 tomatoes..."
        className="w-full px-3 py-2 border border-sand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terra-500 resize-none"
        rows={4}
      />

      <div className="flex items-center justify-between mt-3">
        <p className="text-xs text-sand-500">
          Press Cmd+Enter to submit
        </p>
        <div className="flex space-x-2">
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-sm text-sand-700 bg-sand-100 hover:bg-sand-200 rounded-lg transition-colors"
            disabled={!text.trim()}
          >
            Clear
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-1.5 text-sm text-white bg-herb-500 hover:bg-herb-600 rounded-lg transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed"
            disabled={!text.trim()}
          >
            Add Ingredients
          </button>
        </div>
      </div>
    </div>
  );
}
