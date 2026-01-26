from datetime import UTC, datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    quantity: str
    unit: Optional[str] = None
    raw_input: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IngredientSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    ingredients: list[Ingredient] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["in_progress", "confirmed", "used"] = "in_progress"
