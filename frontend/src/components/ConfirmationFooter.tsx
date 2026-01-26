import React from 'react';

interface ConfirmationFooterProps {
  ingredientCount: number;
  onConfirm: () => void;
  isLoading?: boolean;
}

/**
 * ConfirmationFooter Component
 *
 * Fixed-bottom footer with "Looks good, plan my meals!" button.
 * Shows ingredient count and disables when no ingredients.
 *
 * Features:
 * - Fixed positioning at bottom of screen
 * - Large touch-friendly button
 * - Shows ingredient count
 * - Disabled state when no ingredients
 * - Loading state with spinner
 */
export function ConfirmationFooter({
  ingredientCount,
  onConfirm,
  isLoading = false,
}: ConfirmationFooterProps) {
  const hasIngredients = ingredientCount > 0;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 shadow-lg p-4 safe-area-inset-bottom">
      <div className="max-w-2xl mx-auto">
        {hasIngredients && (
          <p className="text-sm text-gray-600 text-center mb-2">
            {ingredientCount} {ingredientCount === 1 ? 'ingredient' : 'ingredients'} ready
          </p>
        )}

        <button
          onClick={onConfirm}
          disabled={!hasIngredients || isLoading}
          className={`
            w-full py-4 px-6 rounded-lg font-semibold text-lg transition-all
            ${
              hasIngredients && !isLoading
                ? 'bg-green-600 hover:bg-green-700 text-white shadow-md active:scale-95'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
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
              Processing...
            </span>
          ) : (
            'Looks good, plan my meals!'
          )}
        </button>

        {!hasIngredients && (
          <p className="text-xs text-gray-500 text-center mt-2">
            Add ingredients to continue
          </p>
        )}
      </div>
    </div>
  );
}
