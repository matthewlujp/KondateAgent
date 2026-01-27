import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.instagram_client import InstagramClient, InstagramAPIError


@pytest.fixture
def instagram_client():
    """Create InstagramClient with test API key."""
    return InstagramClient(api_key="test-rapidapi-key")


@pytest.fixture
def mock_posts_response():
    """Mock Instagram API response for posts."""
    return {
        "items": [
            {
                "id": "123456789",
                "pk": "123456789",
                "shortcode": "ABC123",
                "caption": {
                    "text": "Delicious pasta recipe! Ingredients: pasta, tomatoes, garlic..."
                },
                "thumbnail_url": "https://example.com/image1.jpg",
                "user": {
                    "username": "chef_account",
                    "pk": "987654321",
                },
                "taken_at": 1705320000,
            },
            {
                "id": "987654321",
                "pk": "987654321",
                "shortcode": "DEF456",
                "caption": {"text": "Quick chicken dinner"},
                "thumbnail_url": "https://example.com/image2.jpg",
                "user": {
                    "username": "food_lover",
                    "pk": "123123123",
                },
                "taken_at": 1705406400,
            },
        ]
    }


@pytest.mark.asyncio
async def test_search_posts_success(instagram_client, mock_posts_response):
    """Test successful post search."""
    with patch.object(instagram_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_posts_response,
            raise_for_status=lambda: None,
        )

        results = await instagram_client.search_posts("pasta recipe")

        assert len(results) == 2
        assert results[0].post_id == "123456789"
        assert results[0].shortcode == "ABC123"
        assert results[0].account_username == "chef_account"
        assert "instagram.com/p/ABC123" in results[0].url


@pytest.mark.asyncio
async def test_search_posts_by_account(instagram_client, mock_posts_response):
    """Test searching posts from specific account."""
    with patch.object(instagram_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_posts_response,
            raise_for_status=lambda: None,
        )

        results = await instagram_client.search_posts("", account_username="chef_account")

        # Verify account endpoint was called
        call_args = mock_get.call_args
        assert "username" in call_args[1]["params"]


@pytest.mark.asyncio
async def test_search_posts_rate_limit(instagram_client):
    """Test handling rate limit error."""
    with patch.object(instagram_client.client, "get") as mock_get:
        from httpx import HTTPStatusError, Response, Request

        mock_response = Response(status_code=429, request=Request("GET", "http://test"))
        mock_get.side_effect = HTTPStatusError("Rate limit", request=mock_response.request, response=mock_response)

        with pytest.raises(InstagramAPIError) as exc_info:
            await instagram_client.search_posts("test")

        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_search_posts_no_api_key():
    """Test error when API key not configured."""
    client = InstagramClient(api_key="")

    with pytest.raises(InstagramAPIError) as exc_info:
        await client.search_posts("test")

    assert "API key not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_posts_account_not_found(instagram_client):
    """Test handling account not found."""
    with patch.object(instagram_client.client, "get") as mock_get:
        from httpx import HTTPStatusError, Response, Request

        mock_response = Response(status_code=404, request=Request("GET", "http://test"))
        mock_get.side_effect = HTTPStatusError("Not found", request=mock_response.request, response=mock_response)

        with pytest.raises(InstagramAPIError) as exc_info:
            await instagram_client.search_posts("", account_username="nonexistent")

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_search_posts_empty_results(instagram_client):
    """Test handling empty search results."""
    with patch.object(instagram_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"items": []},
            raise_for_status=lambda: None,
        )

        results = await instagram_client.search_posts("nonexistent hashtag")

        assert results == []


@pytest.mark.asyncio
async def test_parse_posts_with_invalid_data(instagram_client):
    """Test parsing posts with missing or invalid fields."""
    mock_response = {
        "items": [
            {
                # Valid post
                "id": "123",
                "shortcode": "ABC",
                "caption": {"text": "Test"},
                "thumbnail_url": "https://example.com/image.jpg",
                "user": {"username": "test", "pk": "456"},
                "taken_at": 1705320000,
            },
            {
                # Invalid post - missing shortcode
                "id": "789",
                "caption": {"text": "Invalid"},
            },
            {
                # Invalid post - missing id
                "shortcode": "XYZ",
                "caption": {"text": "Also invalid"},
            },
        ]
    }

    with patch.object(instagram_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None,
        )

        results = await instagram_client.search_posts("test")

        # Should only return valid post
        assert len(results) == 1
        assert results[0].post_id == "123"


@pytest.mark.asyncio
async def test_get_post_details_success(instagram_client):
    """Test getting post details."""
    mock_response = {
        "id": "123456789",
        "shortcode": "ABC123",
        "caption": {"text": "Test post"},
        "thumbnail_url": "https://example.com/image.jpg",
        "user": {"username": "test_user", "pk": "987"},
        "taken_at": 1705320000,
    }

    with patch.object(instagram_client.client, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None,
        )

        result = await instagram_client.get_post_details("ABC123")

        assert result is not None
        assert result.shortcode == "ABC123"
        assert result.account_username == "test_user"


@pytest.mark.asyncio
async def test_get_post_details_not_found(instagram_client):
    """Test getting details for non-existent post."""
    with patch.object(instagram_client.client, "get") as mock_get:
        from httpx import HTTPStatusError, Response, Request

        mock_response = Response(status_code=404, request=Request("GET", "http://test"))
        mock_get.side_effect = HTTPStatusError("Not found", request=mock_response.request, response=mock_response)

        result = await instagram_client.get_post_details("nonexistent")

        assert result is None
