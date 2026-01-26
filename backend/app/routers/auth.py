"""
Authentication endpoints.

Provides simple token generation for development/testing.
TODO: Replace with proper user registration and login in production.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenRequest(BaseModel):
    user_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Generate JWT token for a user.

    WARNING: This is for development only. In production, this should
    require proper authentication (username/password, OAuth, etc.).
    """
    token = create_access_token(request.user_id)
    return TokenResponse(access_token=token)
