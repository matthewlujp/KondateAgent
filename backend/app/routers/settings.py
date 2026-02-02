"""
Settings API router for user preferences
"""
from fastapi import APIRouter, Depends
from app.models.settings import LanguageSettings
from app.services.settings_store import settings_store, SettingsStore

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_settings_store() -> SettingsStore:
    """Dependency injection for settings store"""
    return settings_store


@router.get("/language", response_model=LanguageSettings)
async def get_language_settings(
    store: SettingsStore = Depends(get_settings_store)
) -> LanguageSettings:
    """
    Get current language settings

    Returns default settings if not previously configured
    """
    return store.get_language_settings()


@router.put("/language", response_model=LanguageSettings)
async def update_language_settings(
    settings: LanguageSettings,
    store: SettingsStore = Depends(get_settings_store)
) -> LanguageSettings:
    """
    Update language settings

    Args:
        settings: New language settings to apply

    Returns:
        Updated language settings
    """
    return store.update_language_settings(settings)
