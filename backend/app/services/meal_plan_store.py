from datetime import datetime, UTC
from typing import Optional

from app.models.meal_plan import MealPlan, ChatMessage, RefinementSession


class MealPlanStore:
    """In-memory meal plan store. Replace with database in production."""

    def __init__(self):
        self._plans: dict[str, MealPlan] = {}
        self._user_plans: dict[str, list[str]] = {}  # user_id -> [plan_ids]
        self._sessions: dict[str, RefinementSession] = {}
        self._plan_sessions: dict[str, str] = {}  # plan_id -> session_id

    def save_plan(self, plan: MealPlan) -> MealPlan:
        """Save a meal plan."""
        self._plans[plan.id] = plan

        if plan.user_id not in self._user_plans:
            self._user_plans[plan.user_id] = []
        if plan.id not in self._user_plans[plan.user_id]:
            self._user_plans[plan.user_id].append(plan.id)

        return plan

    def get_plan(self, plan_id: str) -> Optional[MealPlan]:
        """Get a meal plan by ID."""
        return self._plans.get(plan_id)

    def get_latest_plan_by_user(self, user_id: str) -> Optional[MealPlan]:
        """Get the latest meal plan for a user."""
        plan_ids = self._user_plans.get(user_id, [])
        if not plan_ids:
            return None
        return self._plans.get(plan_ids[-1])

    def update_slot_recipe(
        self, plan_id: str, slot_id: str, new_recipe_id: str
    ) -> Optional[MealPlan]:
        """Update a slot's recipe and increment swap_count."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        # Find the slot
        slot_found = False
        for slot in plan.slots:
            if slot.id == slot_id:
                slot.recipe_id = new_recipe_id
                slot.swap_count += 1
                slot.assigned_at = datetime.now(UTC)
                slot_found = True
                break

        if not slot_found:
            return None

        return plan

    def get_or_create_refinement_session(
        self, plan_id: str
    ) -> Optional[RefinementSession]:
        """Get or create a refinement session for a plan."""
        # Check if plan exists
        if plan_id not in self._plans:
            return None

        # Check if session already exists
        if plan_id in self._plan_sessions:
            session_id = self._plan_sessions[plan_id]
            return self._sessions.get(session_id)

        # Create new session
        session = RefinementSession(meal_plan_id=plan_id)
        self._sessions[session.id] = session
        self._plan_sessions[plan_id] = session.id
        return session

    def add_message(
        self, session_id: str, message: ChatMessage
    ) -> Optional[RefinementSession]:
        """Add a message to a refinement session."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.messages.append(message)
        return session


# Singleton instance
meal_plan_store = MealPlanStore()
