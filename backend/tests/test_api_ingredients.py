import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.auth import create_access_token
from app.main import app
from app.models import Ingredient, IngredientSession


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    token = create_access_token("user-123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers():
    """Generate auth headers for a different user."""
    token = create_access_token("user-456")
    return {"Authorization": f"Bearer {token}"}


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

    @pytest.mark.asyncio
    async def test_parse_ingredients_text_too_long(self):
        """Test input validation rejects text over 2000 chars."""
        # Arrange
        long_text = "a" * 2001

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/parse", json={"text": long_text}
            )

        # Assert
        assert response.status_code == 422  # Validation error


class TestSessionEndpoints:
    @pytest.mark.asyncio
    async def test_create_session(self, mock_session_store, auth_headers):
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
                "/api/ingredients/sessions",
                json={"user_id": "user-123"},
                headers=auth_headers,
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
    async def test_create_session_unauthorized(self, mock_session_store):
        """Test create session fails without auth."""
        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/sessions",
                json={"user_id": "user-123"},
            )

        # Assert
        assert response.status_code == 401  # Unauthorized (no auth)

    @pytest.mark.asyncio
    async def test_create_session_for_other_user(self, mock_session_store, auth_headers):
        """Test user cannot create session for another user."""
        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/sessions",
                json={"user_id": "user-456"},  # Different user
                headers=auth_headers,  # Authenticated as user-123
            )

        # Assert
        assert response.status_code == 403
        assert "Cannot create session for another user" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_latest_session(self, mock_session_store, auth_headers):
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
            response = await client.get(
                "/api/ingredients/sessions/latest/user-123",
                headers=auth_headers,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-1"
        assert data["user_id"] == "user-123"
        mock_session_store.get_latest_session.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_get_latest_session_not_found(self, mock_session_store, auth_headers):
        # Arrange
        mock_session_store.get_latest_session.return_value = None

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/ingredients/sessions/latest/user-123",
                headers=auth_headers,
            )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "No session found for user"

    @pytest.mark.asyncio
    async def test_get_latest_session_other_user(self, mock_session_store, auth_headers):
        """Test user cannot access another user's sessions."""
        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/ingredients/sessions/latest/user-456",
                headers=auth_headers,  # Authenticated as user-123
            )

        # Assert
        assert response.status_code == 403
        assert "Cannot access another user's sessions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_ingredients(self, mock_session_store, auth_headers):
        # Arrange
        existing_session = IngredientSession(
            id="session-1",
            user_id="user-123",
            ingredients=[],
        )
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
        mock_session_store.get_session.return_value = existing_session
        mock_session_store.add_ingredients.return_value = updated_session

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/sessions/session-1/ingredients",
                json={
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
                headers=auth_headers,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-1"
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "carrots"

    @pytest.mark.asyncio
    async def test_add_ingredients_other_user_session(self, mock_session_store, auth_headers):
        """Test user cannot add ingredients to another user's session."""
        # Arrange
        other_user_session = IngredientSession(
            id="session-1",
            user_id="user-456",  # Different user
            ingredients=[],
        )
        mock_session_store.get_session.return_value = other_user_session

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ingredients/sessions/session-1/ingredients",
                json={"ingredients": []},
                headers=auth_headers,  # Authenticated as user-123
            )

        # Assert
        assert response.status_code == 403
        assert "Cannot modify another user's session" in response.json()["detail"]
