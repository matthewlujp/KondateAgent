import { apiClient } from './client';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * API client for authentication endpoints.
 */
export const authApi = {
  /**
   * Get JWT token for a user (dev mode only).
   * TODO: Replace with proper login in production.
   */
  async getToken(userId: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/token', {
      user_id: userId,
    });
    return response.data;
  },
};
