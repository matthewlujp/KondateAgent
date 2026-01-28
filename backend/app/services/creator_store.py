from typing import Optional

from app.models.recipe import PreferredCreator


class CreatorStore:
    """In-memory preferred creator store. Replace with database in production."""

    def __init__(self):
        self._creators: dict[str, PreferredCreator] = {}  # creator_id -> PreferredCreator
        self._user_creators: dict[str, list[str]] = {}  # user_id -> [creator_ids]
        self._user_source_creator_index: dict[tuple[str, str, str], str] = {}  # (user_id, source, creator_id) -> creator_id

    def create(self, user_id: str, source: str, creator_id: str, creator_name: str) -> PreferredCreator:
        """Create a new preferred creator for a user."""
        # Check if already exists
        existing_id = self._user_source_creator_index.get((user_id, source, creator_id))
        if existing_id:
            return self._creators[existing_id]

        creator = PreferredCreator(
            user_id=user_id,
            source=source,
            creator_id=creator_id,
            creator_name=creator_name,
        )
        self._creators[creator.id] = creator

        if user_id not in self._user_creators:
            self._user_creators[user_id] = []
        self._user_creators[user_id].append(creator.id)

        self._user_source_creator_index[(user_id, source, creator_id)] = creator.id

        return creator

    def get(self, creator_id: str) -> Optional[PreferredCreator]:
        """Get a preferred creator by ID."""
        return self._creators.get(creator_id)

    def list_by_user(self, user_id: str) -> list[PreferredCreator]:
        """List all preferred creators for a user."""
        creator_ids = self._user_creators.get(user_id, [])
        return [self._creators[cid] for cid in creator_ids if cid in self._creators]

    def delete(self, creator_id: str) -> bool:
        """Delete a preferred creator. Returns True if deleted, False if not found."""
        creator = self._creators.pop(creator_id, None)
        if not creator:
            return False

        # Remove from user's list
        user_creators = self._user_creators.get(creator.user_id, [])
        if creator_id in user_creators:
            user_creators.remove(creator_id)

        # Remove from index
        self._user_source_creator_index.pop(
            (creator.user_id, creator.source, creator.creator_id), None
        )

        return True


# Singleton instance
creator_store = CreatorStore()
