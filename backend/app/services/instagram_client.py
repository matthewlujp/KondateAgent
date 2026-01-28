from datetime import datetime
from typing import Optional
import httpx

from app.config import settings


class InstagramSearchResult:
    """Structured result from Instagram search."""

    def __init__(
        self,
        post_id: str,
        shortcode: str,
        caption: str,
        thumbnail_url: str,
        account_username: str,
        account_id: str,
        posted_at: datetime,
    ):
        self.post_id = post_id
        self.shortcode = shortcode
        self.caption = caption
        self.thumbnail_url = thumbnail_url
        self.account_username = account_username
        self.account_id = account_id
        self.posted_at = posted_at

    @property
    def url(self) -> str:
        return f"https://www.instagram.com/p/{self.shortcode}/"


class InstagramAPIError(Exception):
    """Instagram API error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InstagramClient:
    """
    Client for Instagram via RapidAPI.

    Note: This is a generic implementation. The actual RapidAPI service and endpoints
    may vary. You'll need to adapt this to the specific RapidAPI Instagram service
    you choose (e.g., "Instagram Scraper API", "Instagram Data API", etc.).
    """

    # This is a placeholder - replace with actual RapidAPI service endpoint
    BASE_URL = "https://instagram-scraper-api2.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.instagram_rapidapi_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com",  # Update based on service
            },
        )

    async def search_posts(
        self,
        query: str,
        max_results: int = 10,
        account_username: Optional[str] = None,
    ) -> list[InstagramSearchResult]:
        """
        Search for Instagram posts.

        Args:
            query: Search query (hashtag or keyword)
            max_results: Maximum number of results
            account_username: Optional username to filter results

        Returns:
            List of InstagramSearchResult objects

        Raises:
            InstagramAPIError: If API request fails
        """
        if not self.api_key:
            raise InstagramAPIError("Instagram RapidAPI key not configured")

        # If searching by specific account, use account endpoint
        if account_username:
            return await self._search_by_account(account_username, max_results)

        # Otherwise, search by hashtag/keyword
        return await self._search_by_hashtag(query, max_results)

    async def _search_by_hashtag(self, hashtag: str, max_results: int) -> list[InstagramSearchResult]:
        """
        Search posts by hashtag.

        Note: Endpoint structure depends on the specific RapidAPI service.
        This is a generic implementation that may need adjustment.
        """
        # Remove # if present
        hashtag = hashtag.lstrip("#")

        params = {
            "hashtag": hashtag,
            "count": max_results,
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/v1/hashtag", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise InstagramAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 403:
                raise InstagramAPIError("API key invalid or quota exceeded", 403)
            else:
                raise InstagramAPIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    e.response.status_code,
                )
        except httpx.RequestError as e:
            raise InstagramAPIError(f"Request failed: {str(e)}")

        data = response.json()
        return self._parse_posts(data.get("items", []))

    async def _search_by_account(self, username: str, max_results: int) -> list[InstagramSearchResult]:
        """
        Get recent posts from a specific account.

        Note: Endpoint structure depends on the specific RapidAPI service.
        """
        params = {
            "username": username,
            "count": max_results,
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/v1/posts", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise InstagramAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 403:
                raise InstagramAPIError("API key invalid or quota exceeded", 403)
            elif e.response.status_code == 404:
                raise InstagramAPIError(f"Account '{username}' not found", 404)
            else:
                raise InstagramAPIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    e.response.status_code,
                )
        except httpx.RequestError as e:
            raise InstagramAPIError(f"Request failed: {str(e)}")

        data = response.json()
        return self._parse_posts(data.get("items", []))

    def _parse_posts(self, items: list[dict]) -> list[InstagramSearchResult]:
        """
        Parse Instagram post data into InstagramSearchResult objects.

        Note: Field names depend on the specific RapidAPI service response format.
        This is a generic implementation that may need adjustment.
        """
        results = []
        for item in items:
            try:
                # Common field mappings (adjust based on actual API response)
                post_id = item.get("id") or item.get("pk") or ""
                shortcode = item.get("shortcode") or item.get("code") or ""
                caption_obj = item.get("caption") or {}
                caption = ""
                if isinstance(caption_obj, dict):
                    caption = caption_obj.get("text", "")
                elif isinstance(caption_obj, str):
                    caption = caption_obj

                # Thumbnail URL
                thumbnail_url = ""
                if "thumbnail_url" in item:
                    thumbnail_url = item["thumbnail_url"]
                elif "image_versions2" in item:
                    candidates = item["image_versions2"].get("candidates", [])
                    if candidates:
                        thumbnail_url = candidates[0].get("url", "")
                elif "display_url" in item:
                    thumbnail_url = item["display_url"]

                # Account info
                user = item.get("user") or item.get("owner") or {}
                account_username = user.get("username", "")
                account_id = str(user.get("pk") or user.get("id") or "")

                # Posted timestamp
                taken_at = item.get("taken_at") or item.get("timestamp", 0)
                if isinstance(taken_at, str):
                    posted_at = datetime.fromisoformat(taken_at.replace("Z", "+00:00"))
                else:
                    posted_at = datetime.fromtimestamp(int(taken_at))

                if not post_id or not shortcode:
                    continue  # Skip invalid posts

                results.append(
                    InstagramSearchResult(
                        post_id=post_id,
                        shortcode=shortcode,
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        account_username=account_username,
                        account_id=account_id,
                        posted_at=posted_at,
                    )
                )
            except (KeyError, ValueError, TypeError):
                # Skip posts with parsing errors
                continue

        return results

    async def get_post_details(self, shortcode: str) -> Optional[InstagramSearchResult]:
        """
        Get detailed information about a specific post.

        Args:
            shortcode: Instagram post shortcode

        Returns:
            InstagramSearchResult or None if not found

        Raises:
            InstagramAPIError: If API request fails
        """
        if not self.api_key:
            raise InstagramAPIError("Instagram RapidAPI key not configured")

        params = {"shortcode": shortcode}

        try:
            response = await self.client.get(f"{self.BASE_URL}/v1/post", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise InstagramAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 403:
                raise InstagramAPIError("API key invalid or quota exceeded", 403)
            elif e.response.status_code == 404:
                return None
            else:
                raise InstagramAPIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    e.response.status_code,
                )
        except httpx.RequestError as e:
            raise InstagramAPIError(f"Request failed: {str(e)}")

        data = response.json()
        results = self._parse_posts([data])
        return results[0] if results else None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
