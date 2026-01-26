import React from 'react';
import { Ingredient } from '../types/ingredient';
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
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-16 w-16 text-gray-300 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-700 mb-2">
          No ingredients yet
        </h3>
        <p className="text-sm text-gray-500 max-w-xs">
          Start adding ingredients by voice or text to begin building your meal plan
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 pb-4">
      <div className="text-sm text-gray-600 mb-2">
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
