from datetime import UTC, datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: Literal["youtube", "instagram"]
    source_id: str  # YouTube video ID or Instagram post ID
    url: str  # Direct link to content
    thumbnail_url: str
    title: str
    creator_name: str
    creator_id: str  # Channel ID or Instagram handle
    extracted_ingredients: list[str]  # Parsed from description
    raw_description: str  # Original description for debugging
    duration: Optional[str] = None  # Video length (YouTube only)
    posted_at: datetime
    cached_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cache_expires_at: datetime  # TTL for refresh


class PreferredCreator(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    source: Literal["youtube", "instagram"]
    creator_id: str
    creator_name: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
