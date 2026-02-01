from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx

from app.auth import CurrentUser
from app.models.recipe import PreferredCreator
from app.services.creator_store import creator_store
from app.config import settings

router = APIRouter(prefix="/api/creators", tags=["creators"])


# Request/Response models
class CreateCreatorRequest(BaseModel):
    source: Literal["youtube", "instagram"]
    url: str = Field(description="YouTube channel URL or Instagram profile URL")


class CreateCreatorResponse(BaseModel):
    creator: PreferredCreator
    message: str = Field(description="Success message")


# Endpoints
@router.get("", response_model=list[PreferredCreator])
async def list_creators(current_user: CurrentUser):
    """
    List all preferred creators for the current user.

    Returns creators sorted by most recently added.
    """
    creators = creator_store.list_by_user(current_user)
    # Sort by added_at descending (most recent first)
    creators.sort(key=lambda c: c.added_at, reverse=True)
    return creators


@router.post("", response_model=CreateCreatorResponse, status_code=201)
async def create_creator(request: CreateCreatorRequest, current_user: CurrentUser):
    """
    Add a new preferred creator for the current user.

    Accepts YouTube channel URLs or Instagram profile URLs.
    Extracts creator ID and name from the URL.
    """
    source = request.source
    url = request.url.strip()

    # Extract creator ID and name from URL
    try:
        if source == "youtube":
            creator_id, creator_name = await _parse_youtube_url(url)
        else:  # instagram
            creator_id, creator_name = _parse_instagram_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create preferred creator
    creator = creator_store.create(
        user_id=current_user,
        source=source,
        creator_id=creator_id,
        creator_name=creator_name,
    )

    return CreateCreatorResponse(
        creator=creator,
        message=f"Added {creator_name} to your preferred creators",
    )


@router.delete("/{creator_id}", status_code=204)
async def delete_creator(creator_id: str, current_user: CurrentUser):
    """
    Remove a preferred creator.

    Only the creator's owner can delete it.
    """
    # Get creator to verify ownership
    creator = creator_store.get(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    # Verify ownership
    if creator.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete another user's creator",
        )

    # Delete
    creator_store.delete(creator_id)
    return None


# Helper functions for URL parsing
async def _parse_youtube_url(url: str) -> tuple[str, str]:
    """
    Extract channel ID and name from YouTube URL by calling YouTube API.

    Supports formats:
    - https://www.youtube.com/@channelname (handle format)
    - https://www.youtube.com/c/channelname (custom URL format)
    - https://www.youtube.com/channel/UCxxxxx (direct channel ID)

    Returns:
        Tuple of (channel_id, channel_name)

    Raises:
        ValueError: If URL format is invalid or API call fails
    """
    url = url.rstrip("/")

    if not settings.youtube_api_key:
        raise ValueError("YouTube API key not configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Extract from URL patterns
        if "/@" in url:
            # Handle format: youtube.com/@channelname
            handle = url.split("/@")[-1]
            # Call YouTube API to get channel ID from handle
            params = {
                "part": "id,snippet",
                "forHandle": handle,
                "key": settings.youtube_api_key,
            }
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(f"YouTube channel not found for handle: @{handle}")

            channel_id = data["items"][0]["id"]
            channel_name = data["items"][0]["snippet"]["title"]
            return channel_id, channel_name

        elif "/c/" in url:
            # Handle format: youtube.com/c/channelname (legacy custom URL)
            # These are typically redirected to handles, but we try username lookup
            username = url.split("/c/")[-1]
            params = {
                "part": "id,snippet",
                "forUsername": username,
                "key": settings.youtube_api_key,
            }
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(
                    f"YouTube channel not found for username: {username}. "
                    "Try using the @handle format instead (e.g., youtube.com/@channelname)"
                )

            channel_id = data["items"][0]["id"]
            channel_name = data["items"][0]["snippet"]["title"]
            return channel_id, channel_name

        elif "/channel/" in url:
            # Handle format: youtube.com/channel/UCxxxxx (direct channel ID)
            channel_id = url.split("/channel/")[-1]

            # Fetch channel name from API
            params = {
                "part": "snippet",
                "id": channel_id,
                "key": settings.youtube_api_key,
            }
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(f"YouTube channel not found for ID: {channel_id}")

            channel_name = data["items"][0]["snippet"]["title"]
            return channel_id, channel_name

        else:
            raise ValueError(
                "Invalid YouTube URL format. Supported formats:\n"
                "- youtube.com/@channelname\n"
                "- youtube.com/c/channelname\n"
                "- youtube.com/channel/UCxxxxx"
            )


def _parse_instagram_url(url: str) -> tuple[str, str]:
    """
    Extract username from Instagram URL.

    Supports formats:
    - https://www.instagram.com/username
    - https://instagram.com/username/

    Returns:
        Tuple of (username, username) - Instagram uses username as ID
    """
    url = url.rstrip("/")

    # Extract username from URL
    if "instagram.com/" in url:
        username = url.split("instagram.com/")[-1].split("/")[0]
        # Remove any query params
        username = username.split("?")[0]

        if username:
            return username, username
        else:
            raise ValueError("Could not extract username from Instagram URL")
    else:
        raise ValueError(
            "Invalid Instagram URL. Use format: instagram.com/username"
        )
