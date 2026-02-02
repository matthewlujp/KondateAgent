"""
Settings models for user preferences including language settings
"""
from pydantic import BaseModel, Field
from typing import Literal

SystemLanguage = Literal["en", "ja"]
RecipeLanguage = Literal["en", "ja"]


class LanguageSettings(BaseModel):
    """Language settings for system UI and recipe search"""
    system_language: SystemLanguage = Field(
        default="en",
        description="Language for the user interface",
        alias="systemLanguage"
    )
    recipe_search_languages: list[RecipeLanguage] = Field(
        default_factory=lambda: ["en"],
        description="Languages to use when searching for recipes",
        alias="recipeSearchLanguages"
    )

    model_config = {
        "populate_by_name": True,
        "by_alias": True,
        "json_schema_extra": {
            "example": {
                "systemLanguage": "en",
                "recipeSearchLanguages": ["en", "ja"]
            }
        }
    }
