import { describe, it, expect, vi, beforeEach } from 'vitest';
import { creatorsApi } from '../../api/creators';
import { apiClient } from '../../api/client';

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockCreator = {
  id: 'creator-1',
  user_id: 'user-1',
  source: 'youtube' as const,
  creator_id: 'BabishCulinaryUniverse',
  creator_name: 'BabishCulinaryUniverse',
  added_at: '2026-01-27T00:00:00Z',
};

describe('creatorsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getCreators returns list of creators', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [mockCreator] });

    const result = await creatorsApi.getCreators();

    expect(apiClient.get).toHaveBeenCalledWith('/api/creators');
    expect(result).toEqual([mockCreator]);
  });

  it('addCreator sends source and url', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: { creator: mockCreator, message: 'Added' },
    });

    const result = await creatorsApi.addCreator({
      source: 'youtube',
      url: 'https://www.youtube.com/@BabishCulinaryUniverse',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/creators', {
      source: 'youtube',
      url: 'https://www.youtube.com/@BabishCulinaryUniverse',
    });
    expect(result).toEqual(mockCreator);
  });

  it('deleteCreator calls delete endpoint', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null });

    await creatorsApi.deleteCreator('creator-1');

    expect(apiClient.delete).toHaveBeenCalledWith('/api/creators/creator-1');
  });
});
