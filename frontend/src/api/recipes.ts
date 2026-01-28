import type { ProgressEvent, ScoredRecipe } from '../types';
import { apiClient, tokenManager } from './client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface RecipeSearchResponse {
  recipes: ScoredRecipe[];
}

/**
 * Search for recipes matching user's ingredients (non-streaming).
 *
 * Calls the existing /api/internal/recipes/search endpoint.
 * For streaming progress updates, use streamRecipeSearch instead.
 */
export async function searchRecipes(
  userId: string,
  ingredients: string[],
  maxResults: number = 15
): Promise<ScoredRecipe[]> {
  const response = await apiClient.post<RecipeSearchResponse>(
    '/api/internal/recipes/search',
    {
      user_id: userId,
      ingredients,
      max_results: maxResults,
    }
  );
  return response.data.recipes;
}

export interface StreamRecipeSearchOptions {
  ingredients: string[];
  maxResults?: number;
  onProgress?: (event: ProgressEvent) => void;
  onResult?: (recipes: ScoredRecipe[]) => void;
  onError?: (error: string) => void;
}

/**
 * Stream recipe search with real-time progress updates via Server-Sent Events.
 *
 * Uses fetch() + ReadableStream for SSE since EventSource doesn't support POST
 * or custom headers (needed for JWT auth).
 *
 * Returns AbortController for cancellation.
 */
export async function streamRecipeSearch(
  options: StreamRecipeSearchOptions
): Promise<AbortController> {
  const { ingredients, maxResults = 15, onProgress, onResult, onError } = options;

  const abortController = new AbortController();
  const token = tokenManager.getToken();

  if (!token) {
    onError?.('Authentication required');
    return abortController;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/internal/recipes/search/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ingredients,
        max_results: maxResults,
      }),
      signal: abortController.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      onError?.(errorText || `HTTP ${response.status}`);
      return abortController;
    }

    if (!response.body) {
      onError?.('No response body');
      return abortController;
    }

    // Process SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // Read stream chunks
    const processStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages (separated by \n\n)
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || ''; // Keep incomplete message in buffer

          for (const message of messages) {
            if (!message.trim()) continue;

            // Parse SSE message format: "event: <type>\ndata: <json>"
            const eventMatch = message.match(/^event:\s*(\w+)\n/m);
            const dataMatch = message.match(/^data:\s*(.+)$/m);

            if (!eventMatch || !dataMatch) continue;

            const eventType = eventMatch[1];
            const eventData = dataMatch[1];

            try {
              const parsedData = JSON.parse(eventData);

              switch (eventType) {
                case 'progress':
                  onProgress?.(parsedData as ProgressEvent);
                  break;

                case 'result':
                  onResult?.(parsedData as ScoredRecipe[]);
                  break;

                case 'error':
                  onError?.(parsedData.message || 'Unknown error');
                  break;
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError);
            }
          }
        }
      } catch (error) {
        // Handle abort or network errors
        if (error instanceof Error && error.name !== 'AbortError') {
          onError?.(error.message);
        }
      }
    };

    // Start processing stream (don't await - let it run in background)
    processStream();

  } catch (error) {
    if (error instanceof Error && error.name !== 'AbortError') {
      onError?.(error.message);
    }
  }

  return abortController;
}
