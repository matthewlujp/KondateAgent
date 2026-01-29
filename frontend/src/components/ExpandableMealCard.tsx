import { useState, useId } from 'react';
import type { MealSlot, Recipe } from '../types';

interface ExpandableMealCardProps {
  slot: MealSlot;
  recipe?: Recipe;
}

/**
 * ExpandableMealCard Component
 *
 * Mobile-first meal card with independent expansion capability.
 * Displays a meal slot for a specific day with three possible states:
 * 1. Disabled - Day is skipped (muted appearance, not expandable)
 * 2. Empty - No recipe assigned (placeholder, not expandable)
 * 3. With recipe - Expandable card showing recipe details
 *
 * Features:
 * - Independent expansion (multiple cards can be expanded simultaneously)
 * - Collapsed: shows day, thumbnail, title, creator
 * - Expanded: adds cooking time, ingredients list, description, recipe link
 * - Converts duration from seconds to minutes
 * - Accessible with ARIA labels
 */
export function ExpandableMealCard({ slot, recipe }: ExpandableMealCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentId = useId();
  const buttonId = useId();

  const dayLabel = slot.day.charAt(0).toUpperCase() + slot.day.slice(1);

  // State 1: Disabled day (not expandable)
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

  // State 2: No recipe assigned (not expandable)
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

  // Helper: Convert duration from seconds to minutes
  const durationMinutes = recipe.duration
    ? Math.round(recipe.duration / 60)
    : undefined;

  // State 3: With recipe (expandable)
  return (
    <div className="bg-white border border-sand-200 rounded-lg shadow-warm overflow-hidden">
      {/* Day label */}
      <div className="px-4 pt-3 pb-2 bg-terra-50 border-b border-terra-100">
        <div className="text-sm font-semibold text-terra-700">{dayLabel}</div>
      </div>

      {/* Collapsed header - always visible */}
      <div className="p-4">
        <div className="flex gap-3 items-start">
          {/* Thumbnail */}
          <img
            src={recipe.thumbnail_url}
            alt={recipe.title}
            className="w-20 h-20 rounded-lg object-cover flex-shrink-0 bg-sand-100"
          />

          {/* Title and creator */}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-sand-900 line-clamp-2 mb-1">
              {recipe.title}
            </h3>
            <p className="text-sm text-sand-600">{recipe.creator_name}</p>
          </div>

          {/* Expand/Collapse button */}
          <button
            id={buttonId}
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-shrink-0 p-2 hover:bg-sand-50 rounded-lg transition-colors"
            aria-expanded={isExpanded}
            aria-controls={contentId}
            aria-label={isExpanded ? 'Collapse recipe details' : 'Expand recipe details'}
          >
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
        </div>

        {/* Expanded content */}
        {isExpanded && (
          <div
            id={contentId}
            role="region"
            aria-labelledby={buttonId}
            className="mt-4 pt-4 border-t border-sand-100 space-y-4"
          >
            {/* Cooking time */}
            {durationMinutes !== undefined && (
              <div className="flex items-center gap-2 text-sm text-sand-700">
                <svg
                  className="w-4 h-4"
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
                <span className="font-medium">{durationMinutes} min</span>
              </div>
            )}

            {/* Ingredients */}
            {recipe.extracted_ingredients.length > 0 && (
              <div>
                <div className="text-xs font-medium text-sand-500 mb-2">
                  Ingredients:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {recipe.extracted_ingredients.map((ingredient, idx) => (
                    <span
                      key={idx}
                      className="text-xs bg-sand-100 text-sand-700 px-2 py-1 rounded-full"
                    >
                      {ingredient}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            {recipe.raw_description && (
              <div>
                <div className="text-xs font-medium text-sand-500 mb-2">
                  Description:
                </div>
                <p className="text-sm text-sand-700 leading-relaxed">
                  {recipe.raw_description}
                </p>
              </div>
            )}

            {/* Link to recipe */}
            <div>
              <a
                href={recipe.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-medium text-terra-600 hover:text-terra-700 transition-colors"
              >
                View recipe
                <svg
                  className="w-4 h-4"
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
          </div>
        )}
      </div>
    </div>
  );
}
