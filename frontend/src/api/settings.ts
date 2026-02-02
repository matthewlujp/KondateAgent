/**
 * Settings API client
 */
import { apiClient } from './client';
import type { LanguageSettings } from '../types/language';

/**
 * Get current language settings
 */
export const getLanguageSettings = async (): Promise<LanguageSettings> => {
  const response = await apiClient.get<LanguageSettings>('/api/settings/language');
  return response.data;
};

/**
 * Update language settings
 */
export const updateLanguageSettings = async (
  settings: LanguageSettings
): Promise<LanguageSettings> => {
  const response = await apiClient.put<LanguageSettings>(
    '/api/settings/language',
    settings
  );
  return response.data;
};
