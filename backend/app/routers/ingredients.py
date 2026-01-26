from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import Ingredient, IngredientSession
from app.services.ingredient_parser import IngredientParser
from app.services.session_store import session_store

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])

# Initialize parser
parser = IngredientParser()


# Request/Response models
class ParseRequest(BaseModel):
    text: str


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
async def create_session(request: CreateSessionRequest):
    """Create a new ingredient collection session."""
    session = session_store.create_session(request.user_id)
    return session


@router.get("/sessions/latest/{user_id}", response_model=IngredientSession)
async def get_latest_session(user_id: str):
    """Get the most recent session for a user."""
    session = session_store.get_latest_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No session found for user")
    return session


@router.get("/sessions/{session_id}", response_model=IngredientSession)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/ingredients", response_model=IngredientSession)
async def add_ingredients(session_id: str, request: ParseResponse):
    """Add ingredients to a session."""
    session = session_store.add_ingredients(session_id, request.ingredients)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}/ingredients/{ingredient_id}", response_model=IngredientSession)
async def remove_ingredient(session_id: str, ingredient_id: str):
    """Remove an ingredient from a session."""
    session = session_store.remove_ingredient(session_id, ingredient_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}/status", response_model=IngredientSession)
async def update_status(session_id: str, request: UpdateStatusRequest):
    """Update the status of a session."""
    session = session_store.update_status(session_id, request.status)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
