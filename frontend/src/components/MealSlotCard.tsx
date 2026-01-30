import type { MealSlot, Recipe } from '../types';

interface MealSlotCardProps {
  slot: MealSlot;
  recipe?: Recipe;
}

/**
 * MealSlotCard Component
 *
 * Displays a meal slot for a specific day with three possible states:
 * 1. Disabled - Day is skipped (muted appearance)
 * 2. No recipe - Placeholder when enabled but no recipe assigned
 * 3. With recipe - Full card with recipe details
 *
 * Features:
 * - Displays day label and recipe info
 * - Shows swap count badge when > 0
 * - Links to recipe source
 * - Warm, inviting design with sand/terra theme
 */
export function MealSlotCard({ slot, recipe }: MealSlotCardProps) {
  const dayLabel = slot.day.charAt(0).toUpperCase() + slot.day.slice(1);

  // State 1: Disabled day
  if (!slot.enabled) {
    return (
      <div className="bg-sand-100 border border-sand-200 rounded-lg p-4 opacity-60">
        <div className="text-sm font-medium text-sand-500 mb-2">
          {dayLabel}
        </div>
        <div className="flex items-center justify-center h-20 text-sand-400">
          <svg
            className="w-8 h-8 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
            />
          </svg>
          <span className="text-sm font-medium">Skipped</span>
        </div>
      </div>
    );
  }

  // State 2: No recipe assigned
  if (!slot.recipe_id || !recipe) {
    return (
      <div className="bg-white border-2 border-dashed border-sand-300 rounded-lg p-4">
        <div className="text-sm font-medium text-terra-600 mb-2">
          {dayLabel}
        </div>
        <div className="flex items-center justify-center h-20 text-sand-400">
          <svg
            className="w-8 h-8 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6v6m0 0v6m0-6h6m-6 0H6"
            />
          </svg>
          <span className="text-sm">No recipe assigned</span>
        </div>
      </div>
    );
  }

  // State 3: With recipe
  return (
    <div className="bg-white border border-sand-200 rounded-lg shadow-warm overflow-hidden transition-shadow hover:shadow-lg">
      {/* Day label with swap badge */}
      <div className="px-4 pt-3 pb-2 bg-terra-50 border-b border-terra-100 flex items-center justify-between">
        <div className="text-sm font-semibold text-terra-700">
          {dayLabel}
        </div>
        {slot.swap_count > 0 && (
          <div className="flex items-center text-xs text-terra-600 bg-terra-100 px-2 py-0.5 rounded-full">
            <svg
              className="w-3 h-3 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
            Swapped {slot.swap_count}×
          </div>
        )}
      </div>

      {/* Recipe content */}
      <a
        href={recipe.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block hover:bg-sand-50 transition-colors"
      >
        <div className="p-4">
          {/* Thumbnail and title */}
          <div className="flex gap-3">
            <img
              src={recipe.thumbnail_url}
              alt={recipe.title}
              className="w-20 h-20 rounded-lg object-cover flex-shrink-0 bg-sand-100"
            />
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-semibold text-sand-900 line-clamp-2 mb-1">
                {recipe.title}
              </h3>
              <p className="text-sm text-sand-600">
                {recipe.creator_name}
              </p>
            </div>
          </div>

          {/* Ingredients preview */}
          {recipe.extracted_ingredients.length > 0 && (
            <div className="mt-3 pt-3 border-t border-sand-100">
              <div className="text-xs text-sand-500 mb-1.5">Key ingredients:</div>
              <div className="flex flex-wrap gap-1.5">
                {recipe.extracted_ingredients.slice(0, 4).map((ingredient, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-sand-100 text-sand-700 px-2 py-0.5 rounded-full"
                  >
                    {ingredient}
                  </span>
                ))}
                {recipe.extracted_ingredients.length > 4 && (
                  <span className="text-xs text-sand-500 px-2 py-0.5">
                    +{recipe.extracted_ingredients.length - 4} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </a>
    </div>
  );
}
