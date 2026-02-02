"""
In-memory settings store for user preferences
TODO: Replace with database persistence when user authentication is implemented
"""
from typing import Optional
from app.models.settings import LanguageSettings


class SettingsStore:
    """Simple in-memory storage for settings (temporary until DB is implemented)"""

    def __init__(self):
        # For now, use a single global settings object
        # When auth is added, this will become a dict keyed by user_id
        self._settings: Optional[LanguageSettings] = None

    def get_language_settings(self, user_id: Optional[str] = None) -> LanguageSettings:
        """
        Get language settings for a user

        Args:
            user_id: User identifier (unused until auth is implemented)

        Returns:
            LanguageSettings object with defaults if not set
        """
        if self._settings is None:
            self._settings = LanguageSettings()
        return self._settings

    def update_language_settings(
        self,
        settings: LanguageSettings,
        user_id: Optional[str] = None
    ) -> LanguageSettings:
        """
        Update language settings for a user

        Args:
            settings: New language settings
            user_id: User identifier (unused until auth is implemented)

        Returns:
            Updated LanguageSettings object
        """
        self._settings = settings
        return self._settings


# Global instance (will be dependency-injected in routes)
settings_store = SettingsStore()
