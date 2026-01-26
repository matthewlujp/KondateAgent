import React from 'react';

interface SessionStartModalProps {
  isOpen: boolean;
  ingredientCount: number;
  lastUpdated: string;
  onUpdateExisting: () => void;
  onStartFresh: () => void;
}

/**
 * SessionStartModal Component
 *
 * Modal for returning users with existing ingredient sessions.
 * Offers choice to update existing list or start fresh.
 *
 * Features:
 * - Full-screen modal overlay
 * - Shows previous session info (count, last updated)
 * - Two large action buttons
 * - Dismissible with backdrop click
 */
export function SessionStartModal({
  isOpen,
  ingredientCount,
  lastUpdated,
  onUpdateExisting,
  onStartFresh,
}: SessionStartModalProps) {
  if (!isOpen) {
    return null;
  }

  const formatLastUpdated = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) {
      return 'just now';
    } else if (diffMins < 60) {
      return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onStartFresh}
    >
      <div
        className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome back!</h2>
          <p className="text-gray-600">
            You have an existing list with{' '}
            <span className="font-semibold">{ingredientCount}</span>{' '}
            {ingredientCount === 1 ? 'ingredient' : 'ingredients'}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Last updated {formatLastUpdated(lastUpdated)}
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={onUpdateExisting}
            className="w-full py-4 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-lg transition-colors active:scale-95"
          >
            Update my list
          </button>

          <button
            onClick={onStartFresh}
            className="w-full py-4 px-6 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 rounded-lg font-semibold text-lg transition-colors active:scale-95"
          >
            Start fresh
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-4">
          Starting fresh will clear your previous list
        </p>
      </div>
    </div>
  );
}
