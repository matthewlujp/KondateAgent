from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.models import Ingredient


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class ParsedIngredient(BaseModel):
    name: str
    quantity: str
    unit: Optional[str] = None
    confidence: float


class ParsedIngredientList(BaseModel):
    ingredients: list[ParsedIngredient]


SYSTEM_PROMPT = """You are an ingredient parser. Extract ingredients from natural speech.

Rules:
- Preserve specificity (e.g., "cherry tomatoes" stays "cherry tomatoes", not "tomatoes")
- Handle vague quantities ("some", "a little", "half", "a couple")
- Extract units when mentioned ("2 cups", "1 pound")
- Confidence score 0-1 based on clarity of the input
- Ignore pantry staples: salt, pepper, cooking oil, butter, sugar, flour, common dried spices

Return structured JSON with each ingredient's name, quantity, unit (if any), and confidence score."""


class IngredientParser:
    async def parse(self, text: str) -> list[Ingredient]:
        response = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format=ParsedIngredientList,
        )

        parsed = response.choices[0].message.parsed

        return [
            Ingredient(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                raw_input=text,
                confidence=item.confidence,
            )
            for item in parsed.ingredients
        ]
