import { useState } from 'react';
import type { Ingredient } from '../types/ingredient';

interface IngredientItemProps {
  ingredient: Ingredient;
  onUpdate: (id: string, updates: Partial<Ingredient>) => void;
  onDelete: (id: string) => void;
}

/**
 * IngredientItem Component
 *
 * Displays a single ingredient with tap-to-edit functionality and delete button.
 * Shows visual indicator for low-confidence ingredients (confidence < 0.7).
 *
 * Features:
 * - Tap to edit ingredient name and quantity
 * - Yellow highlight for low-confidence ingredients
 * - Delete button with trash icon
 * - Mobile-first touch-friendly design
 */
export function IngredientItem({ ingredient, onUpdate, onDelete }: IngredientItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(ingredient.name);
  const [editQuantity, setEditQuantity] = useState(ingredient.quantity);

  const isLowConfidence = ingredient.confidence < 0.7;

  const handleSave = () => {
    if (editName.trim()) {
      onUpdate(ingredient.id, {
        name: editName.trim(),
        quantity: editQuantity.trim(),
      });
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditName(ingredient.name);
    setEditQuantity(ingredient.quantity);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <div
      className={`
        flex items-center justify-between p-4 rounded-lg border transition-all
        animate-slide-up shadow-warm hover:shadow-warm-md
        ${isLowConfidence ? 'bg-saffron-50 border-saffron-300' : 'bg-white border-sand-200'}
        ${isEditing ? 'ring-2 ring-terra-500' : ''}
      `}
    >
      {isEditing ? (
        <div className="flex-1 flex flex-col space-y-2">
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={handleKeyDown}
            className="px-2 py-1 border border-sand-300 rounded focus:outline-none focus:ring-2 focus:ring-terra-500"
            placeholder="Ingredient name"
            autoFocus
          />
          <input
            type="text"
            value={editQuantity}
            onChange={(e) => setEditQuantity(e.target.value)}
            onKeyDown={handleKeyDown}
            className="px-2 py-1 border border-sand-300 rounded focus:outline-none focus:ring-2 focus:ring-terra-500"
            placeholder="Quantity"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleSave}
              className="px-3 py-1 bg-herb-500 text-white rounded hover:bg-herb-600 text-sm"
            >
              Save
            </button>
            <button
              onClick={handleCancel}
              className="px-3 py-1 bg-sand-200 text-sand-700 rounded hover:bg-sand-300 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <div
            className="flex-1 cursor-pointer"
            onClick={() => setIsEditing(true)}
          >
            <div className="font-medium text-sand-900">{ingredient.name}</div>
            <div className="text-sm text-sand-600">
              {ingredient.quantity}
              {ingredient.unit && ` ${ingredient.unit}`}
            </div>
            {isLowConfidence && (
              <div className="text-xs text-saffron-700 mt-1">
                Tap to verify
              </div>
            )}
          </div>
          <button
            onClick={() => onDelete(ingredient.id)}
            className="ml-4 p-2 text-sand-400 hover:text-chili-600 hover:bg-chili-50 rounded-full transition-colors"
            aria-label="Delete ingredient"
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
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </>
      )}
    </div>
  );
}
