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
      className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-0 sm:p-4 animate-fade-in"
      onClick={onStartFresh}
    >
      <div
        className="bg-white rounded-t-[24px] sm:rounded-xl shadow-warm-xl max-w-md w-full p-6 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-terra-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-terra-600"
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
          <h2 className="text-2xl font-bold text-sand-900 font-display mb-2">Welcome back!</h2>
          <p className="text-sand-600">
            You have an existing list with{' '}
            <span className="font-semibold">{ingredientCount}</span>{' '}
            {ingredientCount === 1 ? 'ingredient' : 'ingredients'}
          </p>
          <p className="text-sm text-sand-500 mt-1">
            Last updated {formatLastUpdated(lastUpdated)}
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={onUpdateExisting}
            className="w-full py-4 px-6 bg-terra-500 hover:bg-terra-600 text-white rounded-lg font-semibold text-lg transition-all shadow-warm hover:shadow-warm-md active:scale-95"
          >
            Update my list
          </button>

          <button
            onClick={onStartFresh}
            className="w-full py-4 px-6 bg-white hover:bg-sand-50 text-sand-700 border-2 border-sand-300 rounded-lg font-semibold text-lg transition-all active:scale-95"
          >
            Start fresh
          </button>
        </div>

        <p className="text-xs text-sand-500 text-center mt-4">
          Starting fresh will clear your previous list
        </p>
      </div>
    </div>
  );
}
