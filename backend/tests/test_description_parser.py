import pytest
from unittest.mock import AsyncMock, patch

from app.services.description_parser import DescriptionParser, ParsedRecipeIngredients


@pytest.fixture
def parser():
    """Create DescriptionParser instance."""
    return DescriptionParser()


@pytest.fixture
def mock_recipe_response():
    """Mock OpenAI response for a valid recipe."""
    mock_parsed = ParsedRecipeIngredients(
        ingredients=["chicken breast", "pasta", "tomatoes", "garlic", "olive oil", "basil"],
        confidence=0.95,
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
def mock_non_recipe_response():
    """Mock OpenAI response for non-recipe content."""
    mock_parsed = ParsedRecipeIngredients(
        ingredients=[],
        confidence=0.1,
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
async def test_parse_recipe_success(parser, mock_recipe_response):
    """Test successfully parsing a recipe description."""
    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_recipe_response)

        result = await parser.parse(
            title="Easy Chicken Pasta Recipe",
            description="Ingredients: 2 chicken breasts, 1 lb pasta, 3 tomatoes, 4 cloves garlic, olive oil, fresh basil",
        )

        assert len(result.ingredients) == 6
        assert "chicken breast" in result.ingredients
        assert "pasta" in result.ingredients
        assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_parse_non_recipe_content(parser, mock_non_recipe_response):
    """Test parsing non-recipe content (vlog, etc.)."""
    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_non_recipe_response)

        result = await parser.parse(
            title="My Day Vlog - Shopping and Errands",
            description="Today I went shopping and did some errands. No recipe here!",
        )

        assert len(result.ingredients) == 0
        assert result.confidence < 0.5


@pytest.mark.asyncio
async def test_parse_with_vague_recipe(parser):
    """Test parsing recipe with vague ingredient description."""
    mock_parsed = ParsedRecipeIngredients(
        ingredients=["chicken", "vegetables", "rice"],
        confidence=0.6,  # Lower confidence due to vagueness
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        result = await parser.parse(
            title="Healthy Dinner",
            description="Made a healthy dinner with chicken, veggies, and rice",
        )

        assert len(result.ingredients) == 3
        assert result.confidence == 0.6


@pytest.mark.asyncio
async def test_parse_long_description_truncation(parser, mock_recipe_response):
    """Test that long descriptions are truncated."""
    long_description = "A" * 3000  # Longer than 2000 char limit

    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_recipe_response)

        result = await parser.parse(title="Recipe", description=long_description)

        # Verify API was called (description would be truncated internally)
        assert mock_client.beta.chat.completions.parse.called
        call_args = mock_client.beta.chat.completions.parse.call_args
        combined_text = call_args[1]["messages"][1]["content"]

        # Should be truncated to ~2000 chars
        assert len(combined_text) <= 2010  # Some buffer for "..." and title


@pytest.mark.asyncio
async def test_parse_refusal_returns_empty(parser):
    """Test that LLM refusal returns empty result."""
    mock_message = AsyncMock()
    mock_message.refusal = "Cannot parse this content"
    mock_message.parsed = None

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        result = await parser.parse(title="Test", description="Test")

        assert result.ingredients == []
        assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_parse_batch(parser):
    """Test parsing multiple recipes in parallel."""
    mock_parsed_1 = ParsedRecipeIngredients(
        ingredients=["chicken", "rice"],
        confidence=0.9,
    )

    mock_parsed_2 = ParsedRecipeIngredients(
        ingredients=["pasta", "tomato"],
        confidence=0.85,
    )

    # Create two different responses
    def create_mock_response(parsed):
        mock_message = AsyncMock()
        mock_message.refusal = None
        mock_message.parsed = parsed

        mock_choice = AsyncMock()
        mock_choice.message = mock_message

        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        return mock_response

    with patch("app.services.description_parser.openai_client") as mock_client:
        # Return different responses for each call
        mock_client.beta.chat.completions.parse = AsyncMock(
            side_effect=[
                create_mock_response(mock_parsed_1),
                create_mock_response(mock_parsed_2),
            ]
        )

        recipes = [
            ("Chicken Rice", "Recipe with chicken and rice"),
            ("Pasta Dish", "Recipe with pasta and tomato"),
        ]

        results = await parser.parse_batch(recipes)

        assert len(results) == 2
        assert results[0].ingredients == ["chicken", "rice"]
        assert results[1].ingredients == ["pasta", "tomato"]


@pytest.mark.asyncio
async def test_parse_empty_title_and_description(parser, mock_non_recipe_response):
    """Test parsing with empty inputs."""
    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_non_recipe_response)

        result = await parser.parse(title="", description="")

        # Should still call API and return result
        assert result.ingredients == []
        assert result.confidence <= 0.5


@pytest.mark.asyncio
async def test_parse_normalizes_ingredients(parser):
    """Test that ingredients are normalized."""
    mock_parsed = ParsedRecipeIngredients(
        ingredients=["chicken", "tomatoes", "garlic"],  # Normalized (not "2 cloves garlic")
        confidence=0.9,
    )

    mock_message = AsyncMock()
    mock_message.refusal = None
    mock_message.parsed = mock_parsed

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.description_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        result = await parser.parse(
            title="Recipe",
            description="Ingredients: 2 lbs chicken, 5 tomatoes, 3 cloves garlic",
        )

        # Normalized names without quantities
        assert "chicken" in result.ingredients
        assert "tomatoes" in result.ingredients
        assert "garlic" in result.ingredients
