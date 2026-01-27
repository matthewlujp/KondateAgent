import pytest
from unittest.mock import patch
from app.config import Settings


def test_default_sources_enabled():
    """Test that both sources are enabled by default."""
    settings = Settings()
    assert settings.enable_youtube_source is True
    assert settings.enable_instagram_source is True


def test_enabled_sources_property_both():
    """Test enabled_sources property returns both sources."""
    settings = Settings()
    assert settings.enabled_sources == ["youtube", "instagram"]


def test_enabled_sources_property_youtube_only():
    """Test enabled_sources property with only YouTube enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "true", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        assert settings.enabled_sources == ["youtube"]


def test_enabled_sources_property_instagram_only():
    """Test enabled_sources property with only Instagram enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "false", "ENABLE_INSTAGRAM_SOURCE": "true"}):
        settings = Settings()
        assert settings.enabled_sources == ["instagram"]


def test_validate_sources_fails_when_both_disabled():
    """Test that validation fails when both sources are disabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "false", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_sources()
        assert "at least one recipe source must be enabled" in str(exc_info.value).lower()


def test_validate_sources_passes_with_one_enabled():
    """Test that validation passes with at least one source enabled."""
    with patch.dict("os.environ", {"ENABLE_YOUTUBE_SOURCE": "true", "ENABLE_INSTAGRAM_SOURCE": "false"}):
        settings = Settings()
        settings.validate_sources()  # Should not raise
