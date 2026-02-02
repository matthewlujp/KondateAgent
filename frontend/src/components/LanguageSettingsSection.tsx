/**
 * Language Settings Section Component
 * Allows users to configure system language and recipe search languages
 */
import { useTranslation } from 'react-i18next';
import { useLanguageSettings } from '../contexts';
import { SYSTEM_LANGUAGES, RECIPE_LANGUAGES } from '../types/language';
import type { SystemLanguage, RecipeLanguage } from '../types/language';

export function LanguageSettingsSection() {
  const { t } = useTranslation();
  const {
    systemLanguage,
    recipeSearchLanguages,
    setSystemLanguage,
    setRecipeSearchLanguages,
    isLoading,
  } = useLanguageSettings();

  const handleSystemLanguageChange = async (language: SystemLanguage) => {
    try {
      await setSystemLanguage(language);
    } catch (error) {
      console.error('Failed to update system language:', error);
    }
  };

  const handleRecipeLanguageToggle = async (language: RecipeLanguage) => {
    if (!recipeSearchLanguages) return;

    try {
      const isCurrentlySelected = recipeSearchLanguages.includes(language);

      // If unchecking and it's the last one, switch to the other language instead
      if (isCurrentlySelected && recipeSearchLanguages.length === 1) {
        const otherLanguage = RECIPE_LANGUAGES.find(lang => lang.value !== language)?.value;
        if (otherLanguage) {
          await setRecipeSearchLanguages([otherLanguage]);
        }
        return;
      }

      // Normal toggle
      const newLanguages = isCurrentlySelected
        ? recipeSearchLanguages.filter((lang) => lang !== language)
        : [...recipeSearchLanguages, language];

      await setRecipeSearchLanguages(newLanguages);
    } catch (error) {
      console.error('Failed to update recipe search languages:', error);
    }
  };

  return (
    <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-sand-700 mb-1">
          {t('settings.language')}
        </h2>
        <p className="text-sm text-sand-500">
          {t('settings.languageDescription')}
        </p>
      </div>

      {isLoading ? (
        <div className="text-sm text-sand-500">{t('common.loading')}</div>
      ) : (
        <div className="space-y-6">
          {/* System Language */}
          <div>
            <label className="block text-sm font-medium text-sand-700 mb-3">
              {t('settings.displayLanguage')}
            </label>
            <div className="flex gap-3">
              {SYSTEM_LANGUAGES.map((lang) => (
                <button
                  key={lang.value}
                  onClick={() => handleSystemLanguageChange(lang.value)}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all font-medium ${
                    systemLanguage === lang.value
                      ? 'bg-terra-500 border-terra-500 text-white shadow-md'
                      : 'bg-white border-sand-300 text-sand-700 hover:border-terra-300 hover:bg-terra-50'
                  }`}
                  aria-pressed={systemLanguage === lang.value}
                >
                  {lang.label}
                </button>
              ))}
            </div>
          </div>

          {/* Recipe Search Languages */}
          <div>
            <label className="block text-sm font-medium text-sand-700 mb-2">
              {t('settings.recipeSearchLanguages')}
            </label>
            <p className="text-xs text-sand-500 mb-3">
              {t('settings.recipeSearchHint')}
            </p>
            <div className="space-y-2">
              {RECIPE_LANGUAGES.map((lang) => {
                const isSelected = recipeSearchLanguages?.includes(lang.value) ?? false;
                return (
                  <label
                    key={lang.value}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-sage-50 border-sage-300'
                        : 'bg-white border-sand-300 hover:border-sand-400'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleRecipeLanguageToggle(lang.value)}
                      className="w-5 h-5 text-sage-500 border-sand-300 rounded focus:ring-2 focus:ring-sage-500 focus:ring-offset-2"
                    />
                    <span className={`font-medium ${isSelected ? 'text-sage-700' : 'text-sand-700'}`}>
                      {lang.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
