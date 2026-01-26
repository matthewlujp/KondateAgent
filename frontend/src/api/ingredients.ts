import { apiClient } from './client';
import type { ParseResponse, IngredientSession, Ingredient } from '../types';

/**
 * API client for ingredient-related endpoints.
 * Provides methods for parsing text, managing sessions, and manipulating ingredients.
 */

export const ingredientsApi = {
  /**
   * Parse natural language text into structured ingredients.
   * @param text - Raw text describing ingredients (e.g., "2 apples, 1 lb chicken")
   * @returns Parsed ingredients with quantities and units
   */
  async parse(text: string): Promise<ParseResponse> {
    const response = await apiClient.post<ParseResponse>('/api/ingredients/parse', { text });
    return response.data;
  },

  /**
   * Create a new ingredient collection session for a user.
   * @param userId - User identifier
   * @returns New session object
   */
  async createSession(userId: string): Promise<IngredientSession> {
    const response = await apiClient.post<IngredientSession>('/api/ingredients/sessions', {
      user_id: userId,
    });
    return response.data;
  },

  /**
   * Get the latest ingredient session for a user.
   * @param userId - User identifier
   * @returns Latest session or null if no session exists
   */
  async getLatestSession(userId: string): Promise<IngredientSession | null> {
    try {
      const response = await apiClient.get<IngredientSession>(
        `/api/ingredients/sessions/latest/${userId}`
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Get a specific ingredient session by ID.
   * @param sessionId - Session identifier
   * @returns Session object
   */
  async getSession(sessionId: string): Promise<IngredientSession> {
    const response = await apiClient.get<IngredientSession>(
      `/api/ingredients/sessions/${sessionId}`
    );
    return response.data;
  },

  /**
   * Add ingredients to an existing session.
   * @param sessionId - Session identifier
   * @param ingredients - Array of ingredients to add
   * @returns Updated session object
   */
  async addIngredients(
    sessionId: string,
    ingredients: Ingredient[]
  ): Promise<IngredientSession> {
    const response = await apiClient.post<IngredientSession>(
      `/api/ingredients/sessions/${sessionId}/ingredients`,
      { ingredients }
    );
    return response.data;
  },

  /**
   * Remove a specific ingredient from a session.
   * @param sessionId - Session identifier
   * @param ingredientId - Ingredient identifier to remove
   * @returns Updated session object
   */
  async removeIngredient(sessionId: string, ingredientId: string): Promise<IngredientSession> {
    const response = await apiClient.delete<IngredientSession>(
      `/api/ingredients/sessions/${sessionId}/ingredients/${ingredientId}`
    );
    return response.data;
  },

  /**
   * Update the status of an ingredient session.
   * @param sessionId - Session identifier
   * @param status - New status ('in_progress' | 'confirmed' | 'used')
   * @returns Updated session object
   */
  async updateStatus(
    sessionId: string,
    status: 'in_progress' | 'confirmed' | 'used'
  ): Promise<IngredientSession> {
    const response = await apiClient.patch<IngredientSession>(
      `/api/ingredients/sessions/${sessionId}/status`,
      { status }
    );
    return response.data;
  },
};
