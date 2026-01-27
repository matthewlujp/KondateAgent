from datetime import datetime, UTC, timedelta
from typing import Optional
import asyncio

from app.models.recipe import Recipe
from app.services.creator_store import creator_store
from app.services.recipe_cache import recipe_cache
from app.services.query_generator import QueryGenerator
from app.services.youtube_client import YouTubeClient, YouTubeAPIError
from app.services.instagram_client import InstagramClient, InstagramAPIError
from app.services.description_parser import DescriptionParser
from app.services.recipe_matcher import RecipeMatcher, RecipeMatchScore


class ScoredRecipe:
    """Recipe with match score."""

    def __init__(self, recipe: Recipe, score: RecipeMatchScore):
        self.recipe = recipe
        self.score = score


class RecipeCollectionService:
    """
    Orchestrates recipe collection pipeline:
    1. Generate search queries from ingredients
    2. Search YouTube and Instagram (parallel)
    3. Parse descriptions to extract ingredients
    4. Score recipes against user ingredients
    5. Return top-scored recipes
    """

    def __init__(self):
        self.query_generator = QueryGenerator()
        self.youtube_client = YouTubeClient()
        self.instagram_client = InstagramClient()
        self.description_parser = DescriptionParser()
        self.recipe_matcher = RecipeMatcher()

    async def search_recipes(
        self,
        user_id: str,
        ingredients: list[str],
        max_results: int = 15,
    ) -> list[ScoredRecipe]:
        """
        Search for recipes matching user's ingredients.

        Args:
            user_id: User identifier
            ingredients: List of ingredient names user has
            max_results: Maximum number of top recipes to return

        Returns:
            List of ScoredRecipe ordered by match score (best first)

        Raises:
            Exception: If both YouTube and Instagram fail
        """
        # Step 1: Generate search queries
        queries = await self.query_generator.generate(ingredients)
        all_queries = queries.direct_queries + queries.dish_suggestions

        if not all_queries:
            return []

        # Step 2: Get preferred creators for boosting
        preferred_creators = creator_store.list_by_user(user_id)
        youtube_channels = [
            c.creator_id for c in preferred_creators if c.source == "youtube"
        ]
        instagram_accounts = [
            c.creator_id for c in preferred_creators if c.source == "instagram"
        ]

        # Step 3: Search both platforms in parallel
        youtube_results, instagram_results = await self._search_all_platforms(
            all_queries, youtube_channels, instagram_accounts
        )

        if not youtube_results and not instagram_results:
            raise Exception("No recipes found from any source")

        # Step 4: Convert to Recipe objects (with caching)
        recipes = await self._convert_to_recipes(youtube_results, instagram_results)

        if not recipes:
            return []

        # Step 5: Score recipes against user ingredients
        scored_recipes = await self._score_recipes(recipes, ingredients)

        # Step 6: Sort by score and return top N
        scored_recipes.sort(key=lambda sr: sr.score.coverage_score, reverse=True)
        return scored_recipes[:max_results]

    async def _search_all_platforms(
        self,
        queries: list[str],
        youtube_channels: list[str],
        instagram_accounts: list[str],
    ) -> tuple[list, list]:
        """
        Search YouTube and Instagram in parallel.

        Returns:
            Tuple of (youtube_results, instagram_results)
        """
        youtube_task = self._search_youtube(queries, youtube_channels)
        instagram_task = self._search_instagram(queries, instagram_accounts)

        youtube_results, instagram_results = await asyncio.gather(
            youtube_task, instagram_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(youtube_results, Exception):
            youtube_results = []

        if isinstance(instagram_results, Exception):
            instagram_results = []

        return youtube_results, instagram_results

    async def _search_youtube(
        self, queries: list[str], preferred_channels: list[str]
    ) -> list:
        """Search YouTube with all queries."""
        all_results = []

        try:
            # Search preferred channels first if any
            if preferred_channels:
                for channel_id in preferred_channels:
                    for query in queries[:3]:  # Limit queries per channel
                        try:
                            results = await self.youtube_client.search_videos(
                                query, max_results=5, channel_id=channel_id
                            )
                            all_results.extend(results)
                        except YouTubeAPIError:
                            continue

            # General search
            for query in queries[:5]:  # Limit total queries
                try:
                    results = await self.youtube_client.search_videos(
                        query, max_results=8
                    )
                    all_results.extend(results)
                except YouTubeAPIError:
                    continue

        except Exception as e:
            # If all YouTube searches fail, return empty
            pass

        # Deduplicate by video_id
        seen = set()
        unique_results = []
        for result in all_results:
            if result.video_id not in seen:
                seen.add(result.video_id)
                unique_results.append(result)

        return unique_results[:40]  # Cap at 40 results

    async def _search_instagram(
        self, queries: list[str], preferred_accounts: list[str]
    ) -> list:
        """Search Instagram with all queries."""
        all_results = []

        try:
            # Search preferred accounts first if any
            if preferred_accounts:
                for account in preferred_accounts:
                    try:
                        results = await self.instagram_client.search_posts(
                            "", max_results=10, account_username=account
                        )
                        all_results.extend(results)
                    except InstagramAPIError:
                        continue

            # General hashtag search
            for query in queries[:5]:  # Limit total queries
                try:
                    # Convert query to hashtag (first word)
                    hashtag = query.split()[0]
                    results = await self.instagram_client.search_posts(
                        hashtag, max_results=8
                    )
                    all_results.extend(results)
                except InstagramAPIError:
                    continue

        except Exception:
            # If all Instagram searches fail, return empty
            pass

        # Deduplicate by post_id
        seen = set()
        unique_results = []
        for result in all_results:
            if result.post_id not in seen:
                seen.add(result.post_id)
                unique_results.append(result)

        return unique_results[:40]  # Cap at 40 results

    async def _convert_to_recipes(
        self, youtube_results: list, instagram_results: list
    ) -> list[Recipe]:
        """
        Convert search results to Recipe objects.

        Checks cache first, parses new descriptions if needed.
        """
        recipes = []

        # Process YouTube results
        for yt_result in youtube_results:
            # Check cache first
            cached = recipe_cache.get_by_source("youtube", yt_result.video_id)
            if cached:
                recipes.append(cached)
                continue

            # Parse description
            try:
                parsed = await self.description_parser.parse(
                    yt_result.title, yt_result.description
                )

                # Skip if low confidence or no ingredients
                if parsed.confidence < 0.5 or not parsed.ingredients:
                    continue

                # Create recipe
                recipe = Recipe(
                    source="youtube",
                    source_id=yt_result.video_id,
                    url=yt_result.url,
                    thumbnail_url=yt_result.thumbnail_url,
                    title=yt_result.title,
                    creator_name=yt_result.channel_name,
                    creator_id=yt_result.channel_id,
                    extracted_ingredients=parsed.ingredients,
                    raw_description=yt_result.description,
                    duration=yt_result.duration,
                    posted_at=yt_result.published_at,
                    cache_expires_at=datetime.now(UTC) + timedelta(days=30),
                )

                # Cache and add to results
                recipe_cache.put(recipe)
                recipes.append(recipe)

            except Exception:
                # Skip recipes that fail to parse
                continue

        # Process Instagram results
        for ig_result in instagram_results:
            # Check cache first
            cached = recipe_cache.get_by_source("instagram", ig_result.post_id)
            if cached:
                recipes.append(cached)
                continue

            # Parse caption
            try:
                parsed = await self.description_parser.parse(
                    "", ig_result.caption  # Instagram doesn't have separate titles
                )

                # Skip if low confidence or no ingredients
                if parsed.confidence < 0.5 or not parsed.ingredients:
                    continue

                # Create recipe
                recipe = Recipe(
                    source="instagram",
                    source_id=ig_result.post_id,
                    url=ig_result.url,
                    thumbnail_url=ig_result.thumbnail_url,
                    title=ig_result.caption[:100],  # Use first 100 chars as title
                    creator_name=ig_result.account_username,
                    creator_id=ig_result.account_id,
                    extracted_ingredients=parsed.ingredients,
                    raw_description=ig_result.caption,
                    posted_at=ig_result.posted_at,
                    cache_expires_at=datetime.now(UTC) + timedelta(days=30),
                )

                # Cache and add to results
                recipe_cache.put(recipe)
                recipes.append(recipe)

            except Exception:
                # Skip recipes that fail to parse
                continue

        return recipes

    async def _score_recipes(
        self, recipes: list[Recipe], user_ingredients: list[str]
    ) -> list[ScoredRecipe]:
        """Score all recipes against user ingredients."""
        # Prepare batch scoring
        recipe_data = [(r.id, r.extracted_ingredients) for r in recipes]

        # Score in batch
        scores = await self.recipe_matcher.score_batch(user_ingredients, recipe_data)

        # Combine recipes with scores
        scored = []
        for recipe in recipes:
            score = scores.get(recipe.id)
            if score and score.coverage_score > 0.1:  # Filter very low matches
                scored.append(ScoredRecipe(recipe, score))

        return scored

    async def close(self):
        """Close HTTP clients."""
        await self.youtube_client.close()
        await self.instagram_client.close()
