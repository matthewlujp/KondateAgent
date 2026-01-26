import React, { useState } from 'react';

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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
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
          className="text-blue-600 hover:text-blue-700 font-medium text-sm underline"
        >
          Type instead
        </button>
      </div>
    );
  }

  return (
    <div className="border-2 border-gray-300 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-2">
        <label htmlFor="text-input" className="text-sm font-medium text-gray-700">
          Type your ingredients
        </label>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700"
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
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        rows={4}
      />

      <div className="flex items-center justify-between mt-3">
        <p className="text-xs text-gray-500">
          Press Cmd+Enter to submit
        </p>
        <div className="flex space-x-2">
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={!text.trim()}
          >
            Clear
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            disabled={!text.trim()}
          >
            Add Ingredients
          </button>
        </div>
      </div>
    </div>
  );
}
