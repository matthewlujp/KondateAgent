from datetime import datetime, UTC
import pytest

from app.services.creator_store import CreatorStore


@pytest.fixture
def store():
    """Create a fresh CreatorStore for each test."""
    return CreatorStore()


def test_create_creator(store):
    """Test creating a preferred creator."""
    creator = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Gordon Ramsay",
    )

    assert creator.id
    assert creator.user_id == "user123"
    assert creator.source == "youtube"
    assert creator.creator_id == "UCxxxxx"
    assert creator.creator_name == "Gordon Ramsay"
    assert creator.added_at <= datetime.now(UTC)


def test_get_creator(store):
    """Test retrieving a creator by ID."""
    creator = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Chef",
    )

    retrieved = store.get(creator.id)
    assert retrieved is not None
    assert retrieved.id == creator.id
    assert retrieved.creator_name == "Chef"


def test_get_nonexistent_creator(store):
    """Test getting a creator that doesn't exist."""
    result = store.get("nonexistent-id")
    assert result is None


def test_list_by_user(store):
    """Test listing all creators for a user."""
    # Create creators for user1
    creator1 = store.create(
        user_id="user1",
        source="youtube",
        creator_id="UC111",
        creator_name="Chef 1",
    )
    creator2 = store.create(
        user_id="user1",
        source="instagram",
        creator_id="chef2_ig",
        creator_name="Chef 2",
    )

    # Create creator for user2
    creator3 = store.create(
        user_id="user2",
        source="youtube",
        creator_id="UC222",
        creator_name="Chef 3",
    )

    # List for user1
    user1_creators = store.list_by_user("user1")
    assert len(user1_creators) == 2
    creator_ids = {c.id for c in user1_creators}
    assert creator1.id in creator_ids
    assert creator2.id in creator_ids
    assert creator3.id not in creator_ids

    # List for user2
    user2_creators = store.list_by_user("user2")
    assert len(user2_creators) == 1
    assert user2_creators[0].id == creator3.id


def test_list_by_user_empty(store):
    """Test listing creators for user with none."""
    creators = store.list_by_user("nonexistent-user")
    assert creators == []


def test_delete_creator(store):
    """Test deleting a creator."""
    creator = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Chef",
    )

    # Delete
    result = store.delete(creator.id)
    assert result is True

    # Verify deleted
    assert store.get(creator.id) is None

    # Verify not in user's list
    user_creators = store.list_by_user("user123")
    assert len(user_creators) == 0


def test_delete_nonexistent_creator(store):
    """Test deleting a creator that doesn't exist."""
    result = store.delete("nonexistent-id")
    assert result is False


def test_create_duplicate_creator(store):
    """Test that creating duplicate creator returns existing one."""
    # Create first time
    creator1 = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Chef",
    )

    # Create duplicate (same user_id, source, creator_id)
    creator2 = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Chef Updated",  # Even with different name
    )

    # Should return the same creator
    assert creator1.id == creator2.id

    # User should still have only 1 creator
    user_creators = store.list_by_user("user123")
    assert len(user_creators) == 1


def test_create_same_creator_different_users(store):
    """Test that same creator can be added by different users."""
    creator1 = store.create(
        user_id="user1",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Popular Chef",
    )

    creator2 = store.create(
        user_id="user2",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Popular Chef",
    )

    # Should be different creator objects (different users)
    assert creator1.id != creator2.id

    # Each user has their own copy
    user1_creators = store.list_by_user("user1")
    assert len(user1_creators) == 1

    user2_creators = store.list_by_user("user2")
    assert len(user2_creators) == 1


def test_create_multiple_sources(store):
    """Test creating creators from different sources."""
    youtube_creator = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="YouTube Chef",
    )

    instagram_creator = store.create(
        user_id="user123",
        source="instagram",
        creator_id="chef_ig",
        creator_name="Instagram Chef",
    )

    # Both should exist
    creators = store.list_by_user("user123")
    assert len(creators) == 2

    sources = {c.source for c in creators}
    assert "youtube" in sources
    assert "instagram" in sources


def test_delete_one_creator_keeps_others(store):
    """Test that deleting one creator doesn't affect others."""
    creator1 = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UC111",
        creator_name="Chef 1",
    )

    creator2 = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UC222",
        creator_name="Chef 2",
    )

    # Delete creator1
    store.delete(creator1.id)

    # creator2 should still exist
    assert store.get(creator2.id) is not None

    # User should have 1 creator
    creators = store.list_by_user("user123")
    assert len(creators) == 1
    assert creators[0].id == creator2.id


def test_creator_timestamps(store):
    """Test that creator timestamps are set correctly."""
    before = datetime.now(UTC)

    creator = store.create(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Chef",
    )

    after = datetime.now(UTC)

    assert before <= creator.added_at <= after
