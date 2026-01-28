from datetime import datetime, UTC, timedelta
from typing import Optional

from app.models.recipe import Recipe


class RecipeCache:
    """In-memory recipe cache with TTL management. Replace with database in production."""

    def __init__(self, default_ttl_days: int = 30):
        self._recipes: dict[str, Recipe] = {}  # recipe_id -> Recipe
        self._source_index: dict[tuple[str, str], str] = {}  # (source, source_id) -> recipe_id
        self.default_ttl_days = default_ttl_days

    def get(self, recipe_id: str) -> Optional[Recipe]:
        """Get recipe by ID if not expired."""
        recipe = self._recipes.get(recipe_id)
        if recipe and recipe.cache_expires_at > datetime.now(UTC):
            return recipe
        elif recipe:
            # Expired - remove from cache
            self._remove(recipe_id)
        return None

    def get_by_source(self, source: str, source_id: str) -> Optional[Recipe]:
        """Get recipe by source and source_id if not expired."""
        recipe_id = self._source_index.get((source, source_id))
        if recipe_id:
            return self.get(recipe_id)
        return None

    def put(self, recipe: Recipe) -> Recipe:
        """Store or update recipe in cache."""
        # If cache_expires_at not set, use default TTL
        if recipe.cache_expires_at is None or recipe.cache_expires_at <= recipe.cached_at:
            recipe.cache_expires_at = datetime.now(UTC) + timedelta(days=self.default_ttl_days)

        self._recipes[recipe.id] = recipe
        self._source_index[(recipe.source, recipe.source_id)] = recipe.id
        return recipe

    def _remove(self, recipe_id: str) -> None:
        """Remove expired recipe from cache."""
        recipe = self._recipes.pop(recipe_id, None)
        if recipe:
            self._source_index.pop((recipe.source, recipe.source_id), None)

    def cleanup_expired(self) -> int:
        """Remove all expired recipes. Returns count of removed recipes."""
        now = datetime.now(UTC)
        expired_ids = [
            recipe_id
            for recipe_id, recipe in self._recipes.items()
            if recipe.cache_expires_at <= now
        ]
        for recipe_id in expired_ids:
            self._remove(recipe_id)
        return len(expired_ids)


# Singleton instance
recipe_cache = RecipeCache()
