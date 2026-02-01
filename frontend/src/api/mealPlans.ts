import type { MealPlan, GeneratePlanRequest, ChatResponse } from '../types';
import { apiClient } from './client';

/**
 * Generate a new meal plan from recipes and enabled days.
 */
export async function generatePlan(
  request: GeneratePlanRequest
): Promise<MealPlan> {
  const response = await apiClient.post<MealPlan>('/api/meal-plans', request);
  return response.data;
}

/**
 * Get an existing meal plan by ID.
 */
export async function getPlan(planId: string): Promise<MealPlan> {
  const response = await apiClient.get<MealPlan>(`/api/meal-plans/${planId}`);
  return response.data;
}

/**
 * Send a chat message to refine the meal plan.
 */
export async function sendChatMessage(
  planId: string,
  message: string
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    `/api/meal-plans/${planId}/chat`,
    { message }
  );
  return response.data;
}

export const mealPlansApi = {
  generatePlan,
  getPlan,
  sendChatMessage,
};
