from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser
from app.models import Ingredient, IngredientSession
from app.services.ingredient_parser import IngredientParser
from app.services.session_store import session_store

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])

# Initialize parser
parser = IngredientParser()


# Request/Response models
class ParseRequest(BaseModel):
    text: str = Field(max_length=2000, description="Natural language text to parse (max 2000 chars)")


class ParseResponse(BaseModel):
    ingredients: list[Ingredient]


class CreateSessionRequest(BaseModel):
    user_id: str


class UpdateStatusRequest(BaseModel):
    status: Literal["in_progress", "confirmed", "used"]


# Endpoints
@router.post("/parse", response_model=ParseResponse)
async def parse_ingredients(request: ParseRequest):
    """Parse natural language text into structured ingredients."""
    ingredients = await parser.parse(request.text)
    return ParseResponse(ingredients=ingredients)


@router.post("/sessions", response_model=IngredientSession, status_code=201)
async def create_session(request: CreateSessionRequest, current_user: CurrentUser):
    """Create a new ingredient collection session."""
    # Verify user can only create sessions for themselves
    if request.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot create session for another user"
        )
    session = session_store.create_session(request.user_id)
    return session


@router.get("/sessions/latest/{user_id}", response_model=IngredientSession)
async def get_latest_session(user_id: str, current_user: CurrentUser):
    """Get the most recent session for a user."""
    # Verify user can only access their own sessions
    if user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's sessions"
        )
    session = session_store.get_latest_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No session found for user")
    return session


@router.get("/sessions/{session_id}", response_model=IngredientSession)
async def get_session(session_id: str, current_user: CurrentUser):
    """Get a specific session by ID."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Verify user owns this session
    if session.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's session"
        )
    return session


@router.post("/sessions/{session_id}/ingredients", response_model=IngredientSession)
async def add_ingredients(session_id: str, request: ParseResponse, current_user: CurrentUser):
    """Add ingredients to a session."""
    # Verify session exists and user owns it
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify another user's session"
        )
    session = session_store.add_ingredients(session_id, request.ingredients)
    return session


@router.delete("/sessions/{session_id}/ingredients/{ingredient_id}", response_model=IngredientSession)
async def remove_ingredient(session_id: str, ingredient_id: str, current_user: CurrentUser):
    """Remove an ingredient from a session."""
    # Verify session exists and user owns it
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify another user's session"
        )
    session = session_store.remove_ingredient(session_id, ingredient_id)
    return session


@router.patch("/sessions/{session_id}/status", response_model=IngredientSession)
async def update_status(session_id: str, request: UpdateStatusRequest, current_user: CurrentUser):
    """Update the status of a session."""
    # Verify session exists and user owns it
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify another user's session"
        )
    session = session_store.update_status(session_id, request.status)
    return session
