from datetime import datetime, UTC, timedelta
import pytest

from app.models.recipe import Recipe
from app.services.recipe_cache import RecipeCache


@pytest.fixture
def cache():
    """Create a fresh RecipeCache for each test."""
    return RecipeCache(default_ttl_days=30)


@pytest.fixture
def sample_recipe():
    """Create a sample recipe for testing."""
    now = datetime.now(UTC)
    return Recipe(
        source="youtube",
        source_id="test123",
        url="https://youtube.com/watch?v=test123",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Test Recipe",
        creator_name="Test Chef",
        creator_id="chef123",
        extracted_ingredients=["chicken", "rice"],
        raw_description="A test recipe",
        duration="PT10M",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )


def test_cache_put_and_get(cache, sample_recipe):
    """Test storing and retrieving a recipe."""
    # Put recipe
    result = cache.put(sample_recipe)
    assert result.id == sample_recipe.id

    # Get recipe by ID
    retrieved = cache.get(sample_recipe.id)
    assert retrieved is not None
    assert retrieved.id == sample_recipe.id
    assert retrieved.title == "Test Recipe"
    assert retrieved.source_id == "test123"


def test_cache_get_by_source(cache, sample_recipe):
    """Test retrieving recipe by source and source_id."""
    cache.put(sample_recipe)

    # Get by source
    retrieved = cache.get_by_source("youtube", "test123")
    assert retrieved is not None
    assert retrieved.id == sample_recipe.id
    assert retrieved.title == "Test Recipe"


def test_cache_get_nonexistent(cache):
    """Test getting a recipe that doesn't exist."""
    result = cache.get("nonexistent-id")
    assert result is None

    result = cache.get_by_source("youtube", "nonexistent")
    assert result is None


def test_cache_expired_recipe(cache):
    """Test that expired recipes are not returned."""
    now = datetime.now(UTC)

    # Create recipe that already expired
    expired_recipe = Recipe(
        source="youtube",
        source_id="expired123",
        url="https://youtube.com/watch?v=expired123",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Expired Recipe",
        creator_name="Test Chef",
        creator_id="chef123",
        extracted_ingredients=["test"],
        raw_description="Expired",
        posted_at=now - timedelta(days=31),
        cached_at=now - timedelta(days=31),
        cache_expires_at=now - timedelta(days=1),  # Expired 1 day ago
    )

    cache.put(expired_recipe)

    # Should not return expired recipe
    result = cache.get(expired_recipe.id)
    assert result is None

    result = cache.get_by_source("youtube", "expired123")
    assert result is None


def test_cache_cleanup_expired(cache):
    """Test cleanup of expired recipes."""
    now = datetime.now(UTC)

    # Add valid recipe
    valid_recipe = Recipe(
        source="youtube",
        source_id="valid123",
        url="https://youtube.com/watch?v=valid123",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Valid Recipe",
        creator_name="Test Chef",
        creator_id="chef123",
        extracted_ingredients=["test"],
        raw_description="Valid",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )

    # Add expired recipe (manually to bypass put() validation)
    expired_recipe = Recipe(
        source="youtube",
        source_id="expired123",
        url="https://youtube.com/watch?v=expired123",
        thumbnail_url="https://example.com/thumb.jpg",
        title="Expired Recipe",
        creator_name="Test Chef",
        creator_id="chef123",
        extracted_ingredients=["test"],
        raw_description="Expired",
        posted_at=now - timedelta(days=31),
        cached_at=now - timedelta(days=31),
        cache_expires_at=now - timedelta(days=1),
    )

    cache.put(valid_recipe)
    # Manually add expired recipe to bypass put() TTL reset
    cache._recipes[expired_recipe.id] = expired_recipe
    cache._source_index[(expired_recipe.source, expired_recipe.source_id)] = expired_recipe.id

    # Cleanup expired
    removed_count = cache.cleanup_expired()
    assert removed_count == 1

    # Valid recipe still exists
    assert cache.get(valid_recipe.id) is not None

    # Expired recipe removed
    assert cache.get(expired_recipe.id) is None


def test_cache_update_existing(cache, sample_recipe):
    """Test updating an existing recipe in cache."""
    # Put initial recipe
    cache.put(sample_recipe)

    # Update title
    sample_recipe.title = "Updated Title"
    cache.put(sample_recipe)

    # Retrieve and verify update
    retrieved = cache.get(sample_recipe.id)
    assert retrieved.title == "Updated Title"


def test_cache_default_ttl(cache):
    """Test that default TTL is applied when cache_expires_at is not set properly."""
    now = datetime.now(UTC)

    recipe = Recipe(
        source="youtube",
        source_id="ttl_test",
        url="https://youtube.com/watch?v=ttl_test",
        thumbnail_url="https://example.com/thumb.jpg",
        title="TTL Test",
        creator_name="Test Chef",
        creator_id="chef123",
        extracted_ingredients=["test"],
        raw_description="TTL test",
        posted_at=now,
        cached_at=now,
        cache_expires_at=now,  # Set to now (invalid)
    )

    result = cache.put(recipe)

    # Should have applied default TTL (30 days)
    assert result.cache_expires_at > now
    assert result.cache_expires_at <= now + timedelta(days=31)


def test_cache_multiple_recipes(cache):
    """Test caching multiple recipes."""
    now = datetime.now(UTC)

    recipes = []
    for i in range(5):
        recipe = Recipe(
            source="youtube",
            source_id=f"test{i}",
            url=f"https://youtube.com/watch?v=test{i}",
            thumbnail_url="https://example.com/thumb.jpg",
            title=f"Recipe {i}",
            creator_name="Test Chef",
            creator_id="chef123",
            extracted_ingredients=["test"],
            raw_description=f"Recipe {i}",
            posted_at=now,
            cache_expires_at=now + timedelta(days=30),
        )
        cache.put(recipe)
        recipes.append(recipe)

    # Verify all are cached
    for recipe in recipes:
        retrieved = cache.get(recipe.id)
        assert retrieved is not None
        assert retrieved.title == recipe.title


def test_cache_instagram_recipe(cache):
    """Test caching Instagram recipes."""
    now = datetime.now(UTC)

    ig_recipe = Recipe(
        source="instagram",
        source_id="ABC123",
        url="https://www.instagram.com/p/ABC123/",
        thumbnail_url="https://example.com/image.jpg",
        title="Instagram Recipe",
        creator_name="foodie",
        creator_id="123456",
        extracted_ingredients=["pasta", "tomato"],
        raw_description="Instagram post caption",
        posted_at=now,
        cache_expires_at=now + timedelta(days=30),
    )

    cache.put(ig_recipe)

    # Get by source
    retrieved = cache.get_by_source("instagram", "ABC123")
    assert retrieved is not None
    assert retrieved.source == "instagram"
    assert retrieved.source_id == "ABC123"
