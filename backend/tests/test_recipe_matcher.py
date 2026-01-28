import pytest
from unittest.mock import AsyncMock, patch

from app.services.recipe_matcher import RecipeMatcher, RecipeMatchScore


@pytest.fixture
def matcher():
    """Create RecipeMatcher instance."""
    return RecipeMatcher()


@pytest.fixture
def mock_high_match_response():
    """Mock OpenAI response for high coverage match."""
    mock_parsed = RecipeMatchScore(
        coverage_score=0.85,
        missing_ingredients=["basil", "parmesan"],
        reasoning="User has all main ingredients, missing only garnishes",
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    return mock_response


@pytest.fixture
def mock_low_match_response():
    """Mock OpenAI response for low coverage match."""
    mock_parsed = RecipeMatchScore(
        coverage_score=0.25,
        missing_ingredients=["chicken", "pasta", "cream", "mushrooms"],
        reasoning="User has only basic ingredients, missing main components",
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    return mock_response


@pytest.mark.asyncio
async def test_score_high_match(matcher, mock_high_match_response):
    """Test scoring a recipe with high ingredient match."""
    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_high_match_response)

        user_ingredients = ["chicken breast", "tomatoes", "garlic", "pasta", "olive oil"]
        recipe_ingredients = ["chicken breast", "tomatoes", "garlic", "pasta", "olive oil", "basil", "parmesan"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        assert result.coverage_score == 0.85
        assert "basil" in result.missing_ingredients
        assert "parmesan" in result.missing_ingredients
        assert len(result.reasoning) > 0


@pytest.mark.asyncio
async def test_score_low_match(matcher, mock_low_match_response):
    """Test scoring a recipe with low ingredient match."""
    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_low_match_response)

        user_ingredients = ["tomatoes", "onions"]
        recipe_ingredients = ["chicken", "pasta", "cream", "mushrooms", "parmesan"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        assert result.coverage_score == 0.25
        assert len(result.missing_ingredients) > 0


@pytest.mark.asyncio
async def test_score_perfect_match(matcher):
    """Test scoring a recipe where user has all ingredients."""
    mock_parsed = RecipeMatchScore(
        coverage_score=1.0,
        missing_ingredients=[],
        reasoning="User has all required ingredients",
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        user_ingredients = ["chicken", "rice", "broccoli"]
        recipe_ingredients = ["chicken", "rice", "broccoli"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        assert result.coverage_score == 1.0
        assert result.missing_ingredients == []


@pytest.mark.asyncio
async def test_score_empty_recipe_ingredients(matcher):
    """Test scoring when recipe has no ingredients."""
    user_ingredients = ["chicken", "rice"]
    recipe_ingredients = []

    result = await matcher.score(user_ingredients, recipe_ingredients)

    assert result.coverage_score == 0.0
    assert result.missing_ingredients == []
    assert "no ingredients" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_score_empty_user_ingredients(matcher, mock_low_match_response):
    """Test scoring when user has no ingredients."""
    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_low_match_response)

        user_ingredients = []
        recipe_ingredients = ["chicken", "rice", "broccoli"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        # Should still process, but low score
        assert result.coverage_score < 0.5


@pytest.mark.asyncio
async def test_score_refusal_uses_fallback(matcher):
    """Test fallback scoring when LLM refuses."""
    mock_message = AsyncMock()
    mock_message.refusal = "Cannot score"
    mock_message.parsed = None

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        user_ingredients = ["chicken", "rice"]
        recipe_ingredients = ["chicken", "rice", "soy sauce"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        # Fallback should work
        assert 0.0 <= result.coverage_score <= 1.0
        assert isinstance(result.missing_ingredients, list)
        assert "Simple match" in result.reasoning


@pytest.mark.asyncio
async def test_fallback_score_exact_match(matcher):
    """Test fallback scoring with exact matches."""
    user_ingredients = ["chicken", "rice", "broccoli"]
    recipe_ingredients = ["chicken", "rice", "broccoli"]

    result = matcher._fallback_score(user_ingredients, recipe_ingredients)

    assert result.coverage_score == 1.0
    assert result.missing_ingredients == []


@pytest.mark.asyncio
async def test_fallback_score_partial_match(matcher):
    """Test fallback scoring with partial match."""
    user_ingredients = ["chicken", "rice"]
    recipe_ingredients = ["chicken", "rice", "soy sauce", "ginger"]

    result = matcher._fallback_score(user_ingredients, recipe_ingredients)

    assert result.coverage_score == 0.5  # 2/4 = 0.5
    assert "soy sauce" in result.missing_ingredients
    assert "ginger" in result.missing_ingredients


@pytest.mark.asyncio
async def test_fallback_score_substring_matching(matcher):
    """Test that fallback uses substring matching."""
    user_ingredients = ["chicken breast"]
    recipe_ingredients = ["chicken", "rice"]  # "chicken" matches "chicken breast"

    result = matcher._fallback_score(user_ingredients, recipe_ingredients)

    # Should match "chicken" even though not exact
    assert result.coverage_score >= 0.5


@pytest.mark.asyncio
async def test_score_batch(matcher):
    """Test scoring multiple recipes in parallel."""
    mock_parsed_1 = RecipeMatchScore(
        coverage_score=0.9,
        missing_ingredients=["basil"],
        reasoning="Great match",
    )

    mock_parsed_2 = RecipeMatchScore(
        coverage_score=0.6,
        missing_ingredients=["cream", "butter"],
        reasoning="Decent match",
    )

    def create_mock_response(parsed):
        mock_message = AsyncMock()
        mock_message.refusal = None
        mock_message.parsed = parsed

        mock_choice = AsyncMock()
        mock_choice.message = mock_message

        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        return mock_response

    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            side_effect=[
                create_mock_response(mock_parsed_1),
                create_mock_response(mock_parsed_2),
            ]
        )

        user_ingredients = ["chicken", "tomatoes", "pasta"]
        recipes = [
            ("recipe1", ["chicken", "tomatoes", "pasta", "basil"]),
            ("recipe2", ["chicken", "pasta", "cream", "butter"]),
        ]

        results = await matcher.score_batch(user_ingredients, recipes)

        assert len(results) == 2
        assert results["recipe1"].coverage_score == 0.9
        assert results["recipe2"].coverage_score == 0.6


@pytest.mark.asyncio
async def test_score_handles_substitutions(matcher):
    """Test that scoring considers ingredient substitutions."""
    mock_parsed = RecipeMatchScore(
        coverage_score=0.9,
        missing_ingredients=[],
        reasoning="Chicken breast and chicken thigh are interchangeable",
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.recipe_matcher.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        user_ingredients = ["chicken breast"]
        recipe_ingredients = ["chicken thigh"]

        result = await matcher.score(user_ingredients, recipe_ingredients)

        # LLM should recognize substitution
        assert result.coverage_score >= 0.8


@pytest.mark.asyncio
async def test_fallback_score_empty_recipe(matcher):
    """Test fallback with empty recipe ingredients."""
    user_ingredients = ["chicken", "rice"]
    recipe_ingredients = []

    result = matcher._fallback_score(user_ingredients, recipe_ingredients)

    assert result.coverage_score == 0.0
    assert result.missing_ingredients == []
