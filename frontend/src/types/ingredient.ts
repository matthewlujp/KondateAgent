/**
 * TypeScript types for ingredient-related data structures.
 * These types match the backend Pydantic models in backend/app/models/ingredient.py
 */

export interface Ingredient {
  id: string;
  name: string;
  quantity: string;
  unit?: string;
  raw_input: string;
  confidence: number;
  created_at: string;
}

export interface IngredientSession {
  id: string;
  user_id: string;
  ingredients: Ingredient[];
  created_at: string;
  updated_at: string;
  status: 'in_progress' | 'confirmed' | 'used';
}

export interface ParseResponse {
  ingredients: Ingredient[];
}
