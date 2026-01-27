from datetime import datetime
from typing import Optional
import httpx

from app.config import settings


class YouTubeSearchResult:
    """Structured result from YouTube search."""

    def __init__(
        self,
        video_id: str,
        title: str,
        thumbnail_url: str,
        channel_id: str,
        channel_name: str,
        description: str,
        published_at: datetime,
        duration: Optional[str] = None,
    ):
        self.video_id = video_id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.description = description
        self.published_at = published_at
        self.duration = duration

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


class YouTubeAPIError(Exception):
    """YouTube API error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class YouTubeClient:
    """Client for YouTube Data API v3."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.youtube_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        channel_id: Optional[str] = None,
    ) -> list[YouTubeSearchResult]:
        """
        Search for videos on YouTube.

        Args:
            query: Search query string
            max_results: Maximum number of results (1-50)
            channel_id: Optional channel ID to filter results

        Returns:
            List of YouTubeSearchResult objects

        Raises:
            YouTubeAPIError: If API request fails
        """
        if not self.api_key:
            raise YouTubeAPIError("YouTube API key not configured")

        params = {
            "key": self.api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": "relevance",
        }

        if channel_id:
            params["channelId"] = channel_id

        try:
            response = await self.client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise YouTubeAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 403:
                raise YouTubeAPIError("API key invalid or quota exceeded", 403)
            else:
                raise YouTubeAPIError(f"HTTP {e.response.status_code}: {e.response.text}", e.response.status_code)
        except httpx.RequestError as e:
            raise YouTubeAPIError(f"Request failed: {str(e)}")

        data = response.json()
        items = data.get("items", [])

        if not items:
            return []

        # Get video IDs for detailed info (including duration)
        video_ids = [item["id"]["videoId"] for item in items]
        durations = await self._get_video_durations(video_ids)

        results = []
        for item in items:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            # Parse published date
            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))

            # Get best thumbnail (prefer high quality)
            thumbnails = snippet["thumbnails"]
            thumbnail_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )

            results.append(
                YouTubeSearchResult(
                    video_id=video_id,
                    title=snippet["title"],
                    thumbnail_url=thumbnail_url,
                    channel_id=snippet["channelId"],
                    channel_name=snippet["channelTitle"],
                    description=snippet["description"],
                    published_at=published_at,
                    duration=durations.get(video_id),
                )
            )

        return results

    async def _get_video_durations(self, video_ids: list[str]) -> dict[str, str]:
        """
        Get video durations for multiple videos.

        Args:
            video_ids: List of video IDs

        Returns:
            Dict mapping video_id to duration string (ISO 8601 format)
        """
        if not video_ids:
            return {}

        params = {
            "key": self.api_key,
            "id": ",".join(video_ids),
            "part": "contentDetails",
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/videos", params=params)
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError):
            # If duration fetch fails, return empty dict (non-critical)
            return {}

        data = response.json()
        items = data.get("items", [])

        return {
            item["id"]: item["contentDetails"]["duration"]
            for item in items
            if "contentDetails" in item and "duration" in item["contentDetails"]
        }

    async def get_video_details(self, video_id: str) -> Optional[YouTubeSearchResult]:
        """
        Get detailed information about a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            YouTubeSearchResult or None if not found

        Raises:
            YouTubeAPIError: If API request fails
        """
        if not self.api_key:
            raise YouTubeAPIError("YouTube API key not configured")

        params = {
            "key": self.api_key,
            "id": video_id,
            "part": "snippet,contentDetails",
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/videos", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise YouTubeAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 403:
                raise YouTubeAPIError("API key invalid or quota exceeded", 403)
            else:
                raise YouTubeAPIError(f"HTTP {e.response.status_code}: {e.response.text}", e.response.status_code)
        except httpx.RequestError as e:
            raise YouTubeAPIError(f"Request failed: {str(e)}")

        data = response.json()
        items = data.get("items", [])

        if not items:
            return None

        item = items[0]
        snippet = item["snippet"]
        content_details = item.get("contentDetails", {})

        published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))

        thumbnails = snippet["thumbnails"]
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )

        return YouTubeSearchResult(
            video_id=video_id,
            title=snippet["title"],
            thumbnail_url=thumbnail_url,
            channel_id=snippet["channelId"],
            channel_name=snippet["channelTitle"],
            description=snippet.get("description", ""),
            published_at=published_at,
            duration=content_details.get("duration"),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
