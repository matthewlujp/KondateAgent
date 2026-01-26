import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models import Ingredient, IngredientSession


@pytest.fixture
def mock_parser():
    with patch("app.routers.ingredients.parser") as mock:
        mock.parse = AsyncMock()
        yield mock


@pytest.fixture
def mock_session_store():
    with patch("app.routers.ingredients.session_store") as mock:
        yield mock


class TestParseEndpoint:
    @pytest.mark.asyncio
    async def test_parse_ingredients_success(self, mock_parser):
        # Arrange
        mock_parser.parse.return_value = [
            Ingredient(
                name="tomatoes",
                quantity="3",
                unit="whole",
                raw_input="I have 3 tomatoes",
                confidence=0.95,
            )
        ]

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/parse", json={"text": "I have 3 tomatoes"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "tomatoes"
        assert data["ingredients"][0]["quantity"] == "3"
        assert data["ingredients"][0]["unit"] == "whole"
        assert data["ingredients"][0]["confidence"] == 0.95
        mock_parser.parse.assert_called_once_with("I have 3 tomatoes")


class TestSessionEndpoints:
    @pytest.mark.asyncio
    async def test_create_session(self, mock_session_store):
        # Arrange
        mock_session = IngredientSession(
            id="session-1",
            user_id="user-123",
            ingredients=[],
        )
        mock_session_store.create_session.return_value = mock_session

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/session", json={"user_id": "user-123"}
            )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "session-1"
        assert data["user_id"] == "user-123"
        assert data["ingredients"] == []
        assert data["status"] == "in_progress"
        mock_session_store.create_session.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_get_latest_session(self, mock_session_store):
        # Arrange
        mock_session = IngredientSession(
            id="session-1",
            user_id="user-123",
            ingredients=[],
        )
        mock_session_store.get_latest_session.return_value = mock_session

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/ingredients/session/latest?user_id=user-123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-1"
        assert data["user_id"] == "user-123"
        mock_session_store.get_latest_session.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_get_latest_session_not_found(self, mock_session_store):
        # Arrange
        mock_session_store.get_latest_session.return_value = None

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/ingredients/session/latest?user_id=user-456")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "No session found for user"

    @pytest.mark.asyncio
    async def test_update_session_add_ingredients(self, mock_session_store):
        # Arrange
        new_ingredients = [
            Ingredient(
                name="carrots",
                quantity="5",
                unit="whole",
                raw_input="5 carrots",
                confidence=0.9,
            )
        ]
        updated_session = IngredientSession(
            id="session-1",
            user_id="user-123",
            ingredients=new_ingredients,
        )
        mock_session_store.add_ingredients.return_value = updated_session

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/ingredients/session/session-1",
                json={
                    "action": "add_ingredients",
                    "ingredients": [
                        {
                            "name": "carrots",
                            "quantity": "5",
                            "unit": "whole",
                            "raw_input": "5 carrots",
                            "confidence": 0.9,
                        }
                    ],
                },
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-1"
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "carrots"
