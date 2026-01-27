import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from app.auth import create_access_token
from app.main import app
from app.models.recipe import PreferredCreator


class TestListCreatorsEndpoint:
    """Tests for GET /api/creators endpoint."""

    @pytest.mark.asyncio
    async def test_list_creators_success(self):
        """Test listing user's preferred creators."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_creators = [
            PreferredCreator(
                user_id=user_id,
                source="youtube",
                creator_id="UCchannel1",
                creator_name="Chef 1",
            ),
            PreferredCreator(
                user_id=user_id,
                source="instagram",
                creator_id="chef2_ig",
                creator_name="Chef 2",
            ),
        ]

        with patch("app.routers.creators.creator_store.list_by_user", return_value=mock_creators):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/creators", headers=headers)

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                # Check both creators are present (order may vary due to sorting)
                sources = {c["source"] for c in data}
                assert "youtube" in sources
                assert "instagram" in sources

    @pytest.mark.asyncio
    async def test_list_creators_empty(self):
        """Test listing when user has no creators."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.routers.creators.creator_store.list_by_user", return_value=[]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/creators", headers=headers)

                assert response.status_code == 200
                assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_creators_unauthorized(self):
        """Test listing without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/creators")

            assert response.status_code == 401  # Missing credentials


class TestCreateCreatorEndpoint:
    """Tests for POST /api/creators endpoint."""

    @pytest.mark.asyncio
    async def test_create_creator_youtube_success(self):
        """Test adding a YouTube creator."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_creator = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="gordonramsay",
            creator_name="gordonramsay",
        )

        with patch("app.routers.creators.creator_store.create", return_value=mock_creator):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "youtube",
                        "url": "https://www.youtube.com/@gordonramsay",
                    },
                )

                assert response.status_code == 201
                data = response.json()
                assert data["creator"]["creator_name"] == "gordonramsay"
                assert "Added" in data["message"]

    @pytest.mark.asyncio
    async def test_create_creator_instagram_success(self):
        """Test adding an Instagram creator."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_creator = PreferredCreator(
            user_id=user_id,
            source="instagram",
            creator_id="food_lover",
            creator_name="food_lover",
        )

        with patch("app.routers.creators.creator_store.create", return_value=mock_creator):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "instagram",
                        "url": "https://www.instagram.com/food_lover/",
                    },
                )

                assert response.status_code == 201
                data = response.json()
                assert data["creator"]["source"] == "instagram"

    @pytest.mark.asyncio
    async def test_create_creator_youtube_channel_url(self):
        """Test adding YouTube creator with /channel/ URL."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        mock_creator = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="UCxxxxx",
            creator_name="Channel UCxxxxx",
        )

        with patch("app.routers.creators.creator_store.create", return_value=mock_creator):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "youtube",
                        "url": "https://www.youtube.com/channel/UCxxxxx",
                    },
                )

                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_creator_invalid_youtube_url(self):
        """Test adding creator with invalid YouTube URL."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/creators",
                headers=headers,
                json={
                    "source": "youtube",
                    "url": "https://www.google.com",  # Invalid
                },
            )

            assert response.status_code == 400
            assert "Invalid YouTube URL" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_creator_invalid_instagram_url(self):
        """Test adding creator with invalid Instagram URL."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/creators",
                headers=headers,
                json={
                    "source": "instagram",
                    "url": "https://www.google.com",  # Invalid
                },
            )

            assert response.status_code == 400
            assert "Invalid Instagram URL" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_creator_unauthorized(self):
        """Test creating creator without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/creators",
                json={
                    "source": "youtube",
                    "url": "https://www.youtube.com/@test",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_creator_duplicate(self):
        """Test that duplicate creators return the existing one."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        existing_creator = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="chef",
            creator_name="chef",
        )

        # CreatorStore.create returns existing creator for duplicates
        with patch("app.routers.creators.creator_store.create", return_value=existing_creator):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/creators",
                    headers=headers,
                    json={
                        "source": "youtube",
                        "url": "https://www.youtube.com/@chef",
                    },
                )

                assert response.status_code == 201
                assert response.json()["creator"]["creator_id"] == "chef"


class TestDeleteCreatorEndpoint:
    """Tests for DELETE /api/creators/{creator_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_creator_success(self):
        """Test successfully deleting own creator."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        creator_to_delete = PreferredCreator(
            user_id=user_id,
            source="youtube",
            creator_id="UCchannel",
            creator_name="Chef",
        )

        with patch("app.routers.creators.creator_store.get", return_value=creator_to_delete), \
             patch("app.routers.creators.creator_store.delete", return_value=True):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete(
                    f"/api/creators/{creator_to_delete.id}",
                    headers=headers,
                )

                assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_creator_not_found(self):
        """Test deleting non-existent creator."""
        user_id = "test-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.routers.creators.creator_store.get", return_value=None):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete(
                    "/api/creators/nonexistent-id",
                    headers=headers,
                )

                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_creator_wrong_user(self):
        """Test that user cannot delete another user's creator."""
        user_id = "test-user"
        other_user_id = "other-user"
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        other_users_creator = PreferredCreator(
            user_id=other_user_id,  # Different user
            source="youtube",
            creator_id="UCchannel",
            creator_name="Chef",
        )

        with patch("app.routers.creators.creator_store.get", return_value=other_users_creator):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete(
                    f"/api/creators/{other_users_creator.id}",
                    headers=headers,
                )

                assert response.status_code == 403
                assert "Cannot delete another user's creator" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_creator_unauthorized(self):
        """Test deleting creator without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/creators/some-id")

            assert response.status_code == 401
