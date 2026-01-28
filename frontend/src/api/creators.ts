import { apiClient } from './client';
import type { PreferredCreator, AddCreatorRequest } from '../types';

interface CreateCreatorResponse {
  creator: PreferredCreator;
  message: string;
}

export const creatorsApi = {
  async getCreators(): Promise<PreferredCreator[]> {
    const response = await apiClient.get<PreferredCreator[]>('/api/creators');
    return response.data;
  },

  async addCreator(request: AddCreatorRequest): Promise<PreferredCreator> {
    const response = await apiClient.post<CreateCreatorResponse>('/api/creators', {
      source: request.source,
      url: request.url,
    });
    return response.data.creator;
  },

  async deleteCreator(creatorId: string): Promise<void> {
    await apiClient.delete(`/api/creators/${creatorId}`);
  },
};
