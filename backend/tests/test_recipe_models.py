from datetime import datetime, UTC, timedelta
import pytest

from app.models.recipe import Recipe, PreferredCreator


def test_recipe_creation():
    """Test creating a Recipe with all fields."""
    now = datetime.now(UTC)
    expires = now + timedelta(days=30)

    recipe = Recipe(
        source="youtube",
        source_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        title="Delicious Chicken Pasta",
        creator_name="Chef's Kitchen",
        creator_id="UCxxxxx",
        extracted_ingredients=["chicken", "pasta", "tomatoes"],
        raw_description="A simple chicken pasta recipe...",
        duration="PT10M30S",
        posted_at=now,
        cache_expires_at=expires,
    )

    assert recipe.id  # UUID generated
    assert recipe.source == "youtube"
    assert recipe.source_id == "dQw4w9WgXcQ"
    assert recipe.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert recipe.title == "Delicious Chicken Pasta"
    assert recipe.creator_name == "Chef's Kitchen"
    assert recipe.creator_id == "UCxxxxx"
    assert len(recipe.extracted_ingredients) == 3
    assert "chicken" in recipe.extracted_ingredients
    assert recipe.duration == "PT10M30S"
    assert recipe.cached_at <= datetime.now(UTC)
    assert recipe.cache_expires_at == expires


def test_recipe_instagram():
    """Test creating an Instagram Recipe (no duration)."""
    now = datetime.now(UTC)

    recipe = Recipe(
        source="instagram",
        source_id="ABC123",
        url="https://www.instagram.com/p/ABC123/",
        thumbnail_url="https://example.com/image.jpg",
        title="Quick pasta recipe",
        creator_name="foodie_chef",
        creator_id="12345",
        extracted_ingredients=["pasta", "sauce"],
        raw_description="Quick weeknight pasta...",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )

    assert recipe.source == "instagram"
    assert recipe.duration is None  # Instagram doesn't have duration


def test_recipe_default_values():
    """Test Recipe with default values."""
    now = datetime.now(UTC)

    recipe = Recipe(
        source="youtube",
        source_id="test123",
        url="https://youtube.com/watch?v=test123",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Test Recipe",
        creator_name="Test Chef",
        creator_id="test_id",
        extracted_ingredients=["ingredient1"],
        raw_description="Test description",
        posted_at=now,
        cache_expires_at=now + timedelta(days=1),
    )

    # Check defaults
    assert recipe.id  # UUID auto-generated
    assert recipe.cached_at <= datetime.now(UTC)
    assert recipe.duration is None  # Optional field defaults to None


def test_preferred_creator_creation():
    """Test creating a PreferredCreator."""
    creator = PreferredCreator(
        user_id="user123",
        source="youtube",
        creator_id="UCxxxxx",
        creator_name="Gordon Ramsay",
    )

    assert creator.id  # UUID generated
    assert creator.user_id == "user123"
    assert creator.source == "youtube"
    assert creator.creator_id == "UCxxxxx"
    assert creator.creator_name == "Gordon Ramsay"
    assert creator.added_at <= datetime.now(UTC)


def test_preferred_creator_instagram():
    """Test creating an Instagram PreferredCreator."""
    creator = PreferredCreator(
        user_id="user456",
        source="instagram",
        creator_id="chef_account",
        creator_name="chef_account",
    )

    assert creator.source == "instagram"
    assert creator.creator_id == "chef_account"


def test_recipe_source_validation():
    """Test that Recipe source is validated to youtube or instagram."""
    now = datetime.now(UTC)

    # Valid sources
    recipe_yt = Recipe(
        source="youtube",
        source_id="test",
        url="http://test.com",
        thumbnail_url="http://test.com/thumb.jpg",
        title="Test",
        creator_name="Test",
        creator_id="test",
        extracted_ingredients=["test"],
        raw_description="test",
        posted_at=now,
        cache_expires_at=now + timedelta(days=1),
    )
    assert recipe_yt.source == "youtube"

    recipe_ig = Recipe(
        source="instagram",
        source_id="test",
        url="http://test.com",
        thumbnail_url="http://test.com/thumb.jpg",
        title="Test",
        creator_name="Test",
        creator_id="test",
        extracted_ingredients=["test"],
        raw_description="test",
        posted_at=now,
        cache_expires_at=now + timedelta(days=1),
    )
    assert recipe_ig.source == "instagram"

    # Invalid source should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        Recipe(
            source="tiktok",  # Invalid
            source_id="test",
            url="http://test.com",
            thumbnail_url="http://test.com/thumb.jpg",
            title="Test",
            creator_name="Test",
            creator_id="test",
            extracted_ingredients=["test"],
            raw_description="test",
            posted_at=now,
            cache_expires_at=now + timedelta(days=1),
        )
