import pytest
from unittest.mock import AsyncMock, patch

from app.services.ingredient_parser import IngredientParser, ParsedIngredientList, ParsedIngredient
from app.models import Ingredient


@pytest.fixture
def mock_openai_response():
    return ParsedIngredientList(
        ingredients=[
            ParsedIngredient(name="chicken breast", quantity="2", unit="pieces", confidence=0.95),
            ParsedIngredient(name="tomatoes", quantity="3", unit=None, confidence=0.9),
        ]
    )


@pytest.mark.asyncio
async def test_parse_simple_ingredients(mock_openai_response):
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(refusal=None, parsed=mock_openai_response))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("2 chicken breasts and 3 tomatoes")

        assert len(result) == 2
        assert result[0].name == "chicken breast"
        assert result[0].quantity == "2"
        assert result[1].name == "tomatoes"


@pytest.mark.asyncio
async def test_parse_preserves_specificity():
    """Cherry tomatoes should not become just 'tomatoes'"""
    response = ParsedIngredientList(
        ingredients=[
            ParsedIngredient(name="cherry tomatoes", quantity="1", unit="pint", confidence=0.92),
        ]
    )
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(refusal=None, parsed=response))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("a pint of cherry tomatoes")

        assert result[0].name == "cherry tomatoes"
        assert "cherry" in result[0].name


@pytest.mark.asyncio
async def test_parse_handles_vague_quantities():
    response = ParsedIngredientList(
        ingredients=[
            ParsedIngredient(name="rice", quantity="some", unit=None, confidence=0.85),
            ParsedIngredient(name="red onion", quantity="half", unit=None, confidence=0.88),
        ]
    )
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(refusal=None, parsed=response))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("some leftover rice and half a red onion")

        assert result[0].quantity == "some"
        assert result[1].quantity == "half"


@pytest.mark.asyncio
async def test_parse_handles_refusal():
    """Test that parser returns empty list when OpenAI refuses."""
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(refusal="I cannot parse this", parsed=None))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("inappropriate content")

        assert result == []


@pytest.mark.asyncio
async def test_parse_handles_none_parsed():
    """Test that parser returns empty list when parsed is None."""
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(refusal=None, parsed=None))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("unparseable text")

        assert result == []
