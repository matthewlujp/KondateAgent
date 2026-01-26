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


class UpdateSessionRequest(BaseModel):
    action: Literal["add_ingredients", "remove_ingredient", "update_status"]
    ingredients: list[Ingredient] | None = None
    ingredient_id: str | None = None
    status: Literal["in_progress", "confirmed", "used"] | None = None


# Endpoints
@router.post("/parse", response_model=ParseResponse)
async def parse_ingredients(request: ParseRequest):
    """Parse natural language text into structured ingredients."""
    ingredients = await parser.parse(request.text)
    return ParseResponse(ingredients=ingredients)


@router.post("/session", response_model=IngredientSession, status_code=201)
async def create_session(request: CreateSessionRequest):
    """Create a new ingredient collection session."""
    session = session_store.create_session(request.user_id)
    return session


@router.get("/session/latest", response_model=IngredientSession)
async def get_latest_session(user_id: str = Query(...)):
    """Get the most recent session for a user."""
    session = session_store.get_latest_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No session found for user")
    return session


@router.get("/session/{session_id}", response_model=IngredientSession)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/session/{session_id}", response_model=IngredientSession)
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update a session: add ingredients, remove ingredient, or update status."""
    if request.action == "add_ingredients":
        if not request.ingredients:
            raise HTTPException(
                status_code=400, detail="ingredients required for add_ingredients action"
            )
        session = session_store.add_ingredients(session_id, request.ingredients)
    elif request.action == "remove_ingredient":
        if not request.ingredient_id:
            raise HTTPException(
                status_code=400,
                detail="ingredient_id required for remove_ingredient action",
            )
        session = session_store.remove_ingredient(session_id, request.ingredient_id)
    elif request.action == "update_status":
        if not request.status:
            raise HTTPException(
                status_code=400, detail="status required for update_status action"
            )
        session = session_store.update_status(session_id, request.status)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session
