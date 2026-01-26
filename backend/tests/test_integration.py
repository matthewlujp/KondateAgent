import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.auth import create_access_token
from app.main import app
from app.models import Ingredient
from app.services.ingredient_parser import ParsedIngredientList, ParsedIngredient


class TestFullFlow:
    """Integration test for the complete ingredient collection flow."""

    @pytest.mark.asyncio
    async def test_create_session_parse_add_confirm(self):
        """
        Test the full flow:
        1. Create session
        2. Parse ingredients (with mocked OpenAI)
        3. Add parsed ingredients to session
        4. Confirm session status
        5. Verify latest session retrieval
        """
        user_id = "integration-test-user"

        # Create auth token for the user
        token = create_access_token(user_id)
        headers = {"Authorization": f"Bearer {token}"}

        # Mock OpenAI response for ingredient parsing
        mock_parsed_response = ParsedIngredientList(
            ingredients=[
                ParsedIngredient(
                    name="chicken breast",
                    quantity="2",
                    unit="pieces",
                    confidence=0.95
                ),
                ParsedIngredient(
                    name="tomatoes",
                    quantity="3",
                    unit="whole",
                    confidence=0.92
                ),
                ParsedIngredient(
                    name="onion",
                    quantity="1",
                    unit="whole",
                    confidence=0.90
                ),
            ]
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Step 1: Create a new session
            create_response = await client.post(
                "/api/ingredients/sessions",
                json={"user_id": user_id},
                headers=headers,
            )
            assert create_response.status_code == 201
            session_data = create_response.json()
            assert session_data["user_id"] == user_id
            assert session_data["status"] == "in_progress"
            assert session_data["ingredients"] == []
            session_id = session_data["id"]

            # Step 2: Parse ingredients with mocked OpenAI
            with patch("app.services.ingredient_parser.openai_client") as mock_client:
                mock_client.beta.chat.completions.parse = AsyncMock(
                    return_value=AsyncMock(
                        choices=[AsyncMock(message=AsyncMock(refusal=None, parsed=mock_parsed_response))]
                    )
                )

                parse_response = await client.post(
                    "/api/ingredients/parse",
                    json={"text": "I have 2 chicken breasts, 3 tomatoes, and 1 onion"}
                )
                assert parse_response.status_code == 200
                parsed_data = parse_response.json()
                assert len(parsed_data["ingredients"]) == 3
                assert parsed_data["ingredients"][0]["name"] == "chicken breast"
                assert parsed_data["ingredients"][1]["name"] == "tomatoes"
                assert parsed_data["ingredients"][2]["name"] == "onion"

                parsed_ingredients = parsed_data["ingredients"]

            # Step 3: Add parsed ingredients to session
            add_response = await client.post(
                f"/api/ingredients/sessions/{session_id}/ingredients",
                json={"ingredients": parsed_ingredients},
                headers=headers,
            )
            assert add_response.status_code == 200
            updated_session = add_response.json()
            assert len(updated_session["ingredients"]) == 3
            assert updated_session["ingredients"][0]["name"] == "chicken breast"
            assert updated_session["ingredients"][1]["name"] == "tomatoes"
            assert updated_session["ingredients"][2]["name"] == "onion"
            assert updated_session["status"] == "in_progress"

            # Step 4: Confirm session status
            confirm_response = await client.patch(
                f"/api/ingredients/sessions/{session_id}/status",
                json={"status": "confirmed"},
                headers=headers,
            )
            assert confirm_response.status_code == 200
            confirmed_session = confirm_response.json()
            assert confirmed_session["status"] == "confirmed"
            assert len(confirmed_session["ingredients"]) == 3

            # Step 5: Verify latest session retrieval
            latest_response = await client.get(
                f"/api/ingredients/sessions/latest/{user_id}",
                headers=headers,
            )
            assert latest_response.status_code == 200
            latest_session = latest_response.json()
            assert latest_session["id"] == session_id
            assert latest_session["status"] == "confirmed"
            assert len(latest_session["ingredients"]) == 3
            assert latest_session["user_id"] == user_id
