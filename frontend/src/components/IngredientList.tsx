import type { Ingredient } from '../types/ingredient';
import { IngredientItem } from './IngredientItem';

interface IngredientListProps {
  ingredients: Ingredient[];
  onUpdate: (id: string, updates: Partial<Ingredient>) => void;
  onDelete: (id: string) => void;
}

/**
 * IngredientList Component
 *
 * Displays a list of all ingredients with empty state.
 *
 * Features:
 * - Renders list of IngredientItem components
 * - Shows empty state when no ingredients
 * - Scrollable container for many ingredients
 */
export function IngredientList({ ingredients, onUpdate, onDelete }: IngredientListProps) {
  if (ingredients.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        {/* Kitchen bowl with steam illustration */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-20 w-20 text-sand-300 mb-4 animate-float"
          viewBox="0 0 64 64"
          fill="none"
        >
          {/* Steam wisps */}
          <path
            d="M24 12 Q22 8 24 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M32 10 Q30 6 32 2"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M40 12 Q38 8 40 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.6"
          />
          {/* Bowl */}
          <path
            d="M12 28 Q12 24 16 24 H48 Q52 24 52 28 L50 44 Q50 52 42 52 H22 Q14 52 14 44 Z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="2"
          />
          {/* Bowl rim highlight */}
          <ellipse cx="32" cy="26" rx="18" ry="3" fill="currentColor" opacity="0.3" />
        </svg>
        <h3 className="text-lg font-medium text-sand-700 mb-2">
          Your kitchen awaits
        </h3>
        <p className="text-sm text-sand-500 max-w-xs">
          Start adding ingredients by voice or text to begin building your meal plan
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 pb-4">
      <div className="inline-flex items-center px-3 py-1 rounded-full bg-terra-100 text-terra-700 text-sm font-medium mb-2">
        {ingredients.length} {ingredients.length === 1 ? 'ingredient' : 'ingredients'}
      </div>
      {ingredients.map((ingredient) => (
        <IngredientItem
          key={ingredient.id}
          ingredient={ingredient}
          onUpdate={onUpdate}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
