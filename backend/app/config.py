from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str = ""
    youtube_api_key: str = ""
    instagram_rapidapi_key: str = ""

    # Recipe source toggles
    enable_youtube_source: bool = True
    enable_instagram_source: bool = True

    # JWT Settings
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @property
    def enabled_sources(self) -> list[str]:
        """Get list of enabled source names."""
        sources = []
        if self.enable_youtube_source:
            sources.append("youtube")
        if self.enable_instagram_source:
            sources.append("instagram")
        return sources

    def validate_sources(self) -> None:
        """Ensure at least one source is enabled."""
        if not self.enable_youtube_source and not self.enable_instagram_source:
            raise ValueError(
                "At least one recipe source must be enabled. "
                "Set ENABLE_YOUTUBE_SOURCE=true or ENABLE_INSTAGRAM_SOURCE=true"
            )


settings = Settings()
settings.validate_sources()
