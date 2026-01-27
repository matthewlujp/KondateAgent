import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'kondateagent_token';

export const tokenManager = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  },
};

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track if we're currently refreshing the token to avoid multiple simultaneous refreshes
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

// Add response interceptor to handle auth errors and auto-retry with fresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If we get a 401 and haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't try to refresh token for the auth endpoint itself (avoid infinite loop)
      if (originalRequest.url?.includes('/api/auth/token')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        // If we're already refreshing, wait for that to complete
        if (isRefreshing && refreshPromise) {
          await refreshPromise;
        } else {
          // Start token refresh
          isRefreshing = true;
          console.log('Token invalid, refreshing...');

          // Clear the invalid token
          tokenManager.clearToken();

          // Get a fresh token (hardcoded user ID for demo)
          // In production, this would need to be handled differently
          refreshPromise = (async () => {
            const response = await axios.post(`${API_BASE_URL}/api/auth/token`, {
              user_id: 'demo-user',
            });
            const newToken = response.data.access_token;
            tokenManager.setToken(newToken);
            return newToken;
          })();

          await refreshPromise;
          isRefreshing = false;
          refreshPromise = null;
        }

        // Retry the original request with the new token
        const token = tokenManager.getToken();
        if (token) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshPromise = null;
        console.error('Failed to refresh token:', refreshError);
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);
