from datetime import UTC, datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# Type for days of the week
DayOfWeek = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Constant list of all days
ALL_DAYS: list[DayOfWeek] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class MealSlot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    day: DayOfWeek
    enabled: bool = True
    recipe_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    swap_count: int = 0


class MealPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    ingredient_session_id: str
    status: Literal["draft", "active"] = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    slots: list[MealSlot] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: Optional[list[dict]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RefinementSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    meal_plan_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
