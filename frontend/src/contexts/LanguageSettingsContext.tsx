/**
 * Language Settings Context
 * Manages system language (UI) and recipe search languages with backend persistence
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { LanguageSettings, SystemLanguage, RecipeLanguage } from '../types/language';
import { getLanguageSettings, updateLanguageSettings } from '../api/settings';

interface LanguageSettingsContextValue {
  systemLanguage: SystemLanguage;
  recipeSearchLanguages: RecipeLanguage[];
  setSystemLanguage: (language: SystemLanguage) => Promise<void>;
  setRecipeSearchLanguages: (languages: RecipeLanguage[]) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const LanguageSettingsContext = createContext<LanguageSettingsContextValue | undefined>(
  undefined
);

const STORAGE_KEY = 'languageSettings';

export const LanguageSettingsProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { i18n } = useTranslation();
  const [systemLanguage, setSystemLanguageState] = useState<SystemLanguage>('en');
  const [recipeSearchLanguages, setRecipeSearchLanguagesState] = useState<RecipeLanguage[]>([
    'en',
  ]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load settings from backend on mount (with localStorage fallback)
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Try loading from backend
        const settings = await getLanguageSettings();

        setSystemLanguageState(settings.systemLanguage);
        setRecipeSearchLanguagesState(settings.recipeSearchLanguages);

        // Sync i18n with system language
        await i18n.changeLanguage(settings.systemLanguage);

        // Cache in localStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      } catch (err) {
        console.error('Failed to load language settings from backend:', err);

        // Fallback to localStorage cache
        const cached = localStorage.getItem(STORAGE_KEY);
        if (cached) {
          try {
            const settings: LanguageSettings = JSON.parse(cached);
            setSystemLanguageState(settings.systemLanguage);
            setRecipeSearchLanguagesState(settings.recipeSearchLanguages);
            await i18n.changeLanguage(settings.systemLanguage);
          } catch (parseErr) {
            console.error('Failed to parse cached settings:', parseErr);
            setError('Failed to load settings');
            // Keep default state - don't reset
          }
        } else {
          // No cached settings - use defaults (already set in useState)
          setError(null); // Clear error since we're using valid defaults
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, [i18n]);

  // Persist settings to backend and localStorage
  const persistSettings = useCallback(
    async (settings: LanguageSettings) => {
      try {
        setError(null);

        // Update backend
        await updateLanguageSettings(settings);

        // Update localStorage cache
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      } catch (err) {
        console.error('Failed to persist language settings:', err);
        setError('Failed to save settings');
        throw err;
      }
    },
    []
  );

  // Update system language
  const setSystemLanguage = useCallback(
    async (language: SystemLanguage) => {
      const previousLanguage = systemLanguage;
      const previousRecipeLanguages = recipeSearchLanguages;

      try {
        // Optimistically update UI
        setSystemLanguageState(language);
        await i18n.changeLanguage(language);

        // Auto-sync: Add system language to recipe search languages if not present
        const updatedRecipeLanguages = recipeSearchLanguages.includes(language)
          ? recipeSearchLanguages
          : [...recipeSearchLanguages, language];

        setRecipeSearchLanguagesState(updatedRecipeLanguages);

        // Persist to backend
        await persistSettings({
          systemLanguage: language,
          recipeSearchLanguages: updatedRecipeLanguages,
        });
      } catch (err) {
        // Rollback on error
        setSystemLanguageState(previousLanguage);
        setRecipeSearchLanguagesState(previousRecipeLanguages);
        await i18n.changeLanguage(previousLanguage);
        throw err;
      }
    },
    [systemLanguage, recipeSearchLanguages, i18n, persistSettings]
  );

  // Update recipe search languages
  const setRecipeSearchLanguages = useCallback(
    async (languages: RecipeLanguage[]) => {
      const previousLanguages = recipeSearchLanguages;

      try {
        // Optimistically update UI
        setRecipeSearchLanguagesState(languages);

        // Persist to backend
        await persistSettings({
          systemLanguage,
          recipeSearchLanguages: languages,
        });
      } catch (err) {
        // Rollback on error
        setRecipeSearchLanguagesState(previousLanguages);
        throw err;
      }
    },
    [systemLanguage, recipeSearchLanguages, persistSettings]
  );

  const value: LanguageSettingsContextValue = {
    systemLanguage,
    recipeSearchLanguages,
    setSystemLanguage,
    setRecipeSearchLanguages,
    isLoading,
    error,
  };

  return (
    <LanguageSettingsContext.Provider value={value}>
      {children}
    </LanguageSettingsContext.Provider>
  );
};

export const useLanguageSettings = (): LanguageSettingsContextValue => {
  const context = useContext(LanguageSettingsContext);
  if (context === undefined) {
    throw new Error('useLanguageSettings must be used within a LanguageSettingsProvider');
  }
  return context;
};
