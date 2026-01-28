import pytest
from unittest.mock import AsyncMock, patch

from app.services.query_generator import QueryGenerator, SearchQueries


@pytest.fixture
def generator():
    """Create QueryGenerator instance."""
    return QueryGenerator()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI structured output response."""
    mock_parsed = SearchQueries(
        direct_queries=[
            "chicken tomato pasta recipe",
            "garlic chicken recipe",
            "chicken pasta recipe",
        ],
        dish_suggestions=[
            "chicken pomodoro",
            "garlic butter chicken pasta",
            "tuscan chicken",
        ],
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
async def test_generate_success(generator, mock_openai_response):
    """Test successful query generation."""
    with patch("app.services.query_generator.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_openai_response)

        result = await generator.generate(["chicken", "tomatoes", "garlic", "pasta"])

        assert len(result.direct_queries) == 3
        assert len(result.dish_suggestions) == 3
        assert "chicken tomato pasta recipe" in result.direct_queries
        assert "chicken pomodoro" in result.dish_suggestions


@pytest.mark.asyncio
async def test_generate_with_empty_ingredients(generator):
    """Test generating queries with empty ingredient list."""
    result = await generator.generate([])

    assert result.direct_queries == []
    assert result.dish_suggestions == []


@pytest.mark.asyncio
async def test_generate_with_single_ingredient(generator, mock_openai_response):
    """Test generating queries with single ingredient."""
    with patch("app.services.query_generator.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_openai_response)

        result = await generator.generate(["chicken"])

        assert len(result.direct_queries) > 0
        assert len(result.dish_suggestions) > 0


@pytest.mark.asyncio
async def test_generate_fallback_on_refusal(generator):
    """Test fallback query generation when LLM refuses."""
    mock_message = AsyncMock()
    mock_message.refusal = "I cannot generate queries"
    mock_message.parsed = None

    mock_choice = AsyncMock()
    mock_choice.message = mock_message

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.query_generator.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        result = await generator.generate(["chicken", "rice", "broccoli"])

        # Should use fallback
        assert len(result.direct_queries) > 0
        assert "chicken rice recipe" in result.direct_queries
        # Fallback doesn't generate dish suggestions
        assert result.dish_suggestions == []


@pytest.mark.asyncio
async def test_generate_fallback_on_exception(generator):
    """Test fallback when OpenAI API raises exception."""
    with patch("app.services.query_generator.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(side_effect=Exception("API Error"))

        # Should raise the exception (no fallback on API errors)
        with pytest.raises(Exception):
            await generator.generate(["chicken", "rice"])


@pytest.mark.asyncio
async def test_fallback_queries_two_ingredients(generator):
    """Test fallback query generation with 2 ingredients."""
    result = generator._fallback_queries(["chicken", "rice"])

    assert len(result.direct_queries) > 0
    assert "chicken rice recipe" in result.direct_queries
    assert "chicken recipe" in result.direct_queries


@pytest.mark.asyncio
async def test_fallback_queries_three_plus_ingredients(generator):
    """Test fallback query generation with 3+ ingredients."""
    result = generator._fallback_queries(["chicken", "rice", "broccoli", "soy sauce"])

    assert len(result.direct_queries) > 0
    assert "chicken rice recipe" in result.direct_queries
    assert "chicken rice broccoli recipe" in result.direct_queries
    assert "chicken recipe" in result.direct_queries


@pytest.mark.asyncio
async def test_fallback_queries_limits_to_five(generator):
    """Test that fallback limits queries to 5."""
    # Create many ingredients
    ingredients = [f"ingredient{i}" for i in range(20)]

    result = generator._fallback_queries(ingredients)

    assert len(result.direct_queries) <= 5


@pytest.mark.asyncio
async def test_generate_with_many_ingredients(generator, mock_openai_response):
    """Test generating queries with many ingredients."""
    many_ingredients = ["chicken", "rice", "broccoli", "carrots", "onions", "garlic", "soy sauce"]

    with patch("app.services.query_generator.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_openai_response)

        result = await generator.generate(many_ingredients)

        # Should still generate queries
        assert len(result.direct_queries) > 0
        assert len(result.dish_suggestions) > 0
