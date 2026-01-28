import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mealPlansApi } from '../../api/mealPlans';
import { apiClient } from '../../api/client';
import type { MealPlan, ChatResponse } from '../../types';

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockPlan: MealPlan = {
  id: 'plan-1',
  user_id: 'user-1',
  ingredient_session_id: 'session-1',
  status: 'active',
  created_at: '2026-01-27T00:00:00Z',
  slots: [
    {
      id: 'slot-1',
      day: 'monday',
      enabled: true,
      recipe_id: 'recipe-1',
      assigned_at: '2026-01-27T00:00:00Z',
      swap_count: 0,
    },
  ],
};

describe('mealPlansApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('generatePlan sends request and returns plan', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockPlan });

    const request = {
      ingredient_session_id: 'session-1',
      enabled_days: ['monday' as const, 'wednesday' as const],
      recipe_ids: ['recipe-1', 'recipe-2'],
    };

    const result = await mealPlansApi.generatePlan(request);

    expect(apiClient.post).toHaveBeenCalledWith('/api/meal-plans', request);
    expect(result).toEqual(mockPlan);
  });

  it('getPlan fetches plan by ID', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockPlan });

    const result = await mealPlansApi.getPlan('plan-1');

    expect(apiClient.get).toHaveBeenCalledWith('/api/meal-plans/plan-1');
    expect(result).toEqual(mockPlan);
  });

  it('sendChatMessage sends message and returns response', async () => {
    const mockChatResponse: ChatResponse = {
      response: "I'll swap Monday's meal for you.",
      plan: mockPlan,
      tool_calls: [],
    };

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockChatResponse });

    const result = await mealPlansApi.sendChatMessage('plan-1', 'Swap Monday');

    expect(apiClient.post).toHaveBeenCalledWith('/api/meal-plans/plan-1/chat', {
      message: 'Swap Monday',
    });
    expect(result).toEqual(mockChatResponse);
  });
});
