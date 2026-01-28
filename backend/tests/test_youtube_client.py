import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.youtube_client import YouTubeClient, YouTubeAPIError


@pytest.fixture
def youtube_client():
    """Create YouTubeClient with test API key."""
    return YouTubeClient(api_key="test-api-key")


@pytest.fixture
def mock_search_response():
    """Mock YouTube search API response."""
    return {
        "items": [
            {
                "id": {"videoId": "video123"},
                "snippet": {
                    "title": "Chicken Pasta Recipe",
                    "description": "Delicious chicken pasta with tomatoes...",
                    "channelId": "UCxxxxx",
                    "channelTitle": "Chef's Kitchen",
                    "publishedAt": "2024-01-15T12:00:00Z",
                    "thumbnails": {
                        "high": {"url": "https://i.ytimg.com/vi/video123/hqdefault.jpg"}
                    },
                },
            },
            {
                "id": {"videoId": "video456"},
                "snippet": {
                    "title": "Quick Pasta",
                    "description": "Quick weeknight pasta...",
                    "channelId": "UCyyyyy",
                    "channelTitle": "Quick Meals",
                    "publishedAt": "2024-01-16T10:00:00Z",
                    "thumbnails": {
                        "medium": {"url": "https://i.ytimg.com/vi/video456/mqdefault.jpg"}
                    },
                },
            },
        ]
    }


@pytest.fixture
def mock_video_details_response():
    """Mock YouTube videos API response."""
    return {
        "items": [
            {
                "id": "video123",
                "contentDetails": {"duration": "PT10M30S"},
            },
            {
                "id": "video456",
                "contentDetails": {"duration": "PT5M15S"},
            },
        ]
    }


@pytest.mark.asyncio
async def test_search_videos_success(youtube_client, mock_search_response, mock_video_details_response):
    """Test successful video search."""
    with patch.object(youtube_client.client, "get") as mock_get:
        # Mock both search and videos endpoints
        mock_get.side_effect = [
            AsyncMock(
                status_code=200,
                json=lambda: mock_search_response,
                raise_for_status=lambda: None,
            ),
            AsyncMock(
                status_code=200,
                json=lambda: mock_video_details_response,
                raise_for_status=lambda: None,
            ),
        ]

        results = await youtube_client.search_videos("chicken pasta", max_results=10)

        assert len(results) == 2
        assert results[0].video_id == "video123"
        assert results[0].title == "Chicken Pasta Recipe"
        assert results[0].channel_name == "Chef's Kitchen"
        assert results[0].duration == "PT10M30S"
        assert "watch?v=video123" in results[0].url


@pytest.mark.asyncio
async def test_search_videos_with_channel_filter(youtube_client, mock_search_response, mock_video_details_response):
    """Test searching with channel ID filter."""
    with patch.object(youtube_client.client, "get") as mock_get:
        mock_get.side_effect = [
            AsyncMock(status_code=200, json=lambda: mock_search_response, raise_for_status=lambda: None),
            AsyncMock(status_code=200, json=lambda: mock_video_details_response, raise_for_status=lambda: None),
        ]

        results = await youtube_client.search_videos("pasta", channel_id="UCxxxxx")

        # Verify channel ID was passed
        call_args = mock_get.call_args_list[0]
        assert call_args[1]["params"]["channelId"] == "UCxxxxx"


@pytest.mark.asyncio
async def test_search_videos_rate_limit(youtube_client):
    """Test handling rate limit error."""
    with patch.object(youtube_client.client, "get") as mock_get:
        from httpx import HTTPStatusError, Response, Request

        mock_response = Response(status_code=429, request=Request("GET", "http://test"))
        mock_get.side_effect = HTTPStatusError("Rate limit", request=mock_response.request, response=mock_response)

        with pytest.raises(YouTubeAPIError) as exc_info:
            await youtube_client.search_videos("test")

        assert exc_info.value.status_code == 429
        assert "Rate limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_videos_quota_exceeded(youtube_client):
    """Test handling quota exceeded error."""
    with patch.object(youtube_client.client, "get") as mock_get:
        from httpx import HTTPStatusError, Response, Request

        mock_response = Response(status_code=403, request=Request("GET", "http://test"))
        mock_get.side_effect = HTTPStatusError("Forbidden", request=mock_response.request, response=mock_response)

        with pytest.raises(YouTubeAPIError) as exc_info:
            await youtube_client.search_videos("test")

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_search_videos_no_api_key():
    """Test error when API key not configured."""
    client = YouTubeClient(api_key="")

    with pytest.raises(YouTubeAPIError) as exc_info:
        await client.search_videos("test")

    assert "YouTube API key not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_videos_empty_results(youtube_client):
    """Test handling empty search results."""
    with patch.object(youtube_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"items": []},
            raise_for_status=lambda: None,
        )

        results = await youtube_client.search_videos("nonexistent query")

        assert results == []


@pytest.mark.asyncio
async def test_get_video_details_success(youtube_client):
    """Test getting video details."""
    mock_response = {
        "items": [
            {
                "id": "video123",
                "snippet": {
                    "title": "Test Video",
                    "description": "Test description",
                    "channelId": "UCtest",
                    "channelTitle": "Test Channel",
                    "publishedAt": "2024-01-15T12:00:00Z",
                    "thumbnails": {
                        "high": {"url": "https://i.ytimg.com/vi/video123/hqdefault.jpg"}
                    },
                },
                "contentDetails": {
                    "duration": "PT10M",
                },
            }
        ]
    }

    with patch.object(youtube_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None,
        )

        result = await youtube_client.get_video_details("video123")

        assert result is not None
        assert result.video_id == "video123"
        assert result.title == "Test Video"
        assert result.duration == "PT10M"


@pytest.mark.asyncio
async def test_get_video_details_not_found(youtube_client):
    """Test getting details for non-existent video."""
    with patch.object(youtube_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"items": []},
            raise_for_status=lambda: None,
        )

        result = await youtube_client.get_video_details("nonexistent")

        assert result is None


@pytest.mark.asyncio
async def test_thumbnail_url_fallback(youtube_client):
    """Test thumbnail URL selection with fallbacks."""
    mock_response = {
        "items": [
            {
                "id": {"videoId": "video123"},
                "snippet": {
                    "title": "Test",
                    "description": "Test",
                    "channelId": "UCtest",
                    "channelTitle": "Test",
                    "publishedAt": "2024-01-15T12:00:00Z",
                    "thumbnails": {
                        # No high quality, should fall back to medium
                        "medium": {"url": "https://medium.jpg"},
                        "default": {"url": "https://default.jpg"},
                    },
                },
            }
        ]
    }

    with patch.object(youtube_client.client, "get") as mock_get:
        mock_get.side_effect = [
            AsyncMock(status_code=200, json=lambda: mock_response, raise_for_status=lambda: None),
            AsyncMock(status_code=200, json=lambda: {"items": []}, raise_for_status=lambda: None),
        ]

        results = await youtube_client.search_videos("test")

        assert results[0].thumbnail_url == "https://medium.jpg"
