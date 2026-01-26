from datetime import datetime, UTC
from typing import Literal, Optional

from app.models import Ingredient, IngredientSession


class SessionStore:
    """In-memory session store. Replace with database in production."""

    def __init__(self):
        self._sessions: dict[str, IngredientSession] = {}
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> [session_ids]

    def create_session(self, user_id: str) -> IngredientSession:
        session = IngredientSession(user_id=user_id)
        self._sessions[session.id] = session

        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.id)

        return session

    def get_session(self, session_id: str) -> Optional[IngredientSession]:
        return self._sessions.get(session_id)

    def get_latest_session(self, user_id: str) -> Optional[IngredientSession]:
        session_ids = self._user_sessions.get(user_id, [])
        if not session_ids:
            return None
        return self._sessions.get(session_ids[-1])

    def add_ingredients(
        self, session_id: str, ingredients: list[Ingredient]
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.ingredients.extend(ingredients)
        session.updated_at = datetime.now(UTC)
        return session

    def remove_ingredient(
        self, session_id: str, ingredient_id: str
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.ingredients = [
            ing for ing in session.ingredients if ing.id != ingredient_id
        ]
        session.updated_at = datetime.now(UTC)
        return session

    def update_status(
        self, session_id: str, status: Literal["in_progress", "confirmed", "used"]
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.status = status
        session.updated_at = datetime.now(UTC)
        return session


# Singleton instance
session_store = SessionStore()
