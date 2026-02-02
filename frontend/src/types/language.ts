/**
 * Language Settings Types
 * Defines types for system language (UI) and recipe search languages
 */

export type SystemLanguage = 'en' | 'ja';
export type RecipeLanguage = 'en' | 'ja';

export interface LanguageSettings {
  systemLanguage: SystemLanguage;
  recipeSearchLanguages: RecipeLanguage[];
}

export const SYSTEM_LANGUAGES: { value: SystemLanguage; label: string }[] = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
];

export const RECIPE_LANGUAGES: { value: RecipeLanguage; label: string }[] = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
];
