# Ingredient Collection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the voice-first ingredient collection feature that allows users to speak their fridge contents and see them parsed in real-time.

**Architecture:** FastAPI backend with OpenAI Structured Outputs for parsing, React frontend with Web Speech API for voice input. Session-based storage for ingredient lists. Mobile-first responsive design.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, OpenAI API, React 18, Vite, TypeScript, TailwindCSS

---

## Phase 1: Backend Foundation

### Task 1: Project Setup - Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/app backend/tests
touch backend/app/__init__.py backend/tests/__init__.py
```

**Step 2: Create requirements.txt**

```text
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
openai==1.12.0
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

**Step 3: Create pyproject.toml**

```toml
[project]
name = "kondate-agent"
version = "0.1.0"
description = "AI-powered meal planning from your fridge ingredients"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 4: Create .env.example**

```bash
OPENAI_API_KEY=your_key_here
```

**Step 5: Create minimal FastAPI app**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KondateAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 6: Verify setup**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload &
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
pkill -f uvicorn
```

**Step 7: Commit**

```bash
git add backend/
git commit -m "feat: initialize backend with FastAPI"
```

---

### Task 2: Ingredient Data Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/ingredient.py`
- Create: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_models.py
import pytest
from app.models.ingredient import Ingredient, IngredientSession


def test_ingredient_creation():
    ingredient = Ingredient(
        name="chicken breast",
        quantity="2",
        raw_input="2 chicken breasts",
        confidence=0.95,
    )
    assert ingredient.name == "chicken breast"
    assert ingredient.quantity == "2"
    assert ingredient.confidence == 0.95
    assert ingredient.id is not None


def test_ingredient_session_creation():
    session = IngredientSession(user_id="user_123")
    assert session.user_id == "user_123"
    assert session.ingredients == []
    assert session.status == "in_progress"
    assert session.id is not None


def test_session_add_ingredient():
    session = IngredientSession(user_id="user_123")
    ingredient = Ingredient(
        name="tomatoes",
        quantity="3",
        raw_input="3 tomatoes",
        confidence=0.9,
    )
    session.ingredients.append(ingredient)
    assert len(session.ingredients) == 1
    assert session.ingredients[0].name == "tomatoes"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_models.py -v
# Expected: FAIL - ModuleNotFoundError: No module named 'app.models'
```

**Step 3: Create models directory**

```bash
mkdir -p backend/app/models
touch backend/app/models/__init__.py
```

**Step 4: Write the Ingredient model**

```python
# backend/app/models/ingredient.py
from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    quantity: str
    unit: Optional[str] = None
    raw_input: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngredientSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    ingredients: list[Ingredient] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["in_progress", "confirmed", "used"] = "in_progress"
```

**Step 5: Export from __init__.py**

```python
# backend/app/models/__init__.py
from .ingredient import Ingredient, IngredientSession

__all__ = ["Ingredient", "IngredientSession"]
```

**Step 6: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_models.py -v
# Expected: 3 passed
```

**Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: add Ingredient and IngredientSession models"
```

---

### Task 3: OpenAI Ingredient Parser Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/ingredient_parser.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/test_ingredient_parser.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_ingredient_parser.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.ingredient_parser import IngredientParser
from app.models import Ingredient


@pytest.fixture
def mock_openai_response():
    return {
        "ingredients": [
            {"name": "chicken breast", "quantity": "2", "unit": "pieces", "confidence": 0.95},
            {"name": "tomatoes", "quantity": "3", "unit": None, "confidence": 0.9},
        ]
    }


@pytest.mark.asyncio
async def test_parse_simple_ingredients(mock_openai_response):
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(parsed=mock_openai_response))]
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
    response = {
        "ingredients": [
            {"name": "cherry tomatoes", "quantity": "1", "unit": "pint", "confidence": 0.92},
        ]
    }
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(parsed=response))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("a pint of cherry tomatoes")

        assert result[0].name == "cherry tomatoes"
        assert "cherry" in result[0].name


@pytest.mark.asyncio
async def test_parse_handles_vague_quantities():
    response = {
        "ingredients": [
            {"name": "rice", "quantity": "some", "unit": None, "confidence": 0.85},
            {"name": "red onion", "quantity": "half", "unit": None, "confidence": 0.88},
        ]
    }
    with patch("app.services.ingredient_parser.openai_client") as mock_client:
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(parsed=response))]
            )
        )

        parser = IngredientParser()
        result = await parser.parse("some leftover rice and half a red onion")

        assert result[0].quantity == "some"
        assert result[1].quantity == "half"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_ingredient_parser.py -v
# Expected: FAIL - ModuleNotFoundError
```

**Step 3: Create config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 4: Write the IngredientParser service**

```python
# backend/app/services/ingredient_parser.py
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
```

**Step 5: Export from __init__.py**

```python
# backend/app/services/__init__.py
from .ingredient_parser import IngredientParser

__all__ = ["IngredientParser"]
```

**Step 6: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_ingredient_parser.py -v
# Expected: 3 passed
```

**Step 7: Commit**

```bash
git add backend/app/services/ backend/app/config.py backend/tests/test_ingredient_parser.py
git commit -m "feat: add OpenAI-powered ingredient parser service"
```

---

### Task 4: In-Memory Session Store

**Files:**
- Create: `backend/app/services/session_store.py`
- Create: `backend/tests/test_session_store.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_session_store.py
import pytest
from app.services.session_store import SessionStore
from app.models import Ingredient, IngredientSession


@pytest.fixture
def store():
    return SessionStore()


@pytest.fixture
def sample_ingredient():
    return Ingredient(
        name="chicken",
        quantity="2",
        raw_input="2 chicken breasts",
        confidence=0.9,
    )


def test_create_session(store):
    session = store.create_session("user_123")
    assert session.user_id == "user_123"
    assert session.status == "in_progress"
    assert len(session.ingredients) == 0


def test_get_session(store):
    created = store.create_session("user_123")
    retrieved = store.get_session(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_nonexistent_session(store):
    result = store.get_session("nonexistent")
    assert result is None


def test_get_latest_session(store):
    store.create_session("user_123")
    latest = store.create_session("user_123")

    result = store.get_latest_session("user_123")
    assert result is not None
    assert result.id == latest.id


def test_add_ingredients(store, sample_ingredient):
    session = store.create_session("user_123")
    updated = store.add_ingredients(session.id, [sample_ingredient])

    assert updated is not None
    assert len(updated.ingredients) == 1
    assert updated.ingredients[0].name == "chicken"


def test_remove_ingredient(store, sample_ingredient):
    session = store.create_session("user_123")
    store.add_ingredients(session.id, [sample_ingredient])

    updated = store.remove_ingredient(session.id, sample_ingredient.id)
    assert updated is not None
    assert len(updated.ingredients) == 0


def test_update_session_status(store):
    session = store.create_session("user_123")
    updated = store.update_status(session.id, "confirmed")

    assert updated is not None
    assert updated.status == "confirmed"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_session_store.py -v
# Expected: FAIL - ModuleNotFoundError
```

**Step 3: Write the SessionStore**

```python
# backend/app/services/session_store.py
from datetime import datetime
from typing import Literal, Optional

from app.models import Ingredient, IngredientSession


class SessionStore:
    """In-memory session store. Replace with database in production."""

    def __init__(self):
        self._sessions: dict[str, IngredientSession] = {}
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> [session_ids]

    def create_session(self, user_id: str) -> IngredientSession:
        session = IngredientSession(user_id=user_id)
        self._sessions[session.id] = session

        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.id)

        return session

    def get_session(self, session_id: str) -> Optional[IngredientSession]:
        return self._sessions.get(session_id)

    def get_latest_session(self, user_id: str) -> Optional[IngredientSession]:
        session_ids = self._user_sessions.get(user_id, [])
        if not session_ids:
            return None
        return self._sessions.get(session_ids[-1])

    def add_ingredients(
        self, session_id: str, ingredients: list[Ingredient]
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.ingredients.extend(ingredients)
        session.updated_at = datetime.utcnow()
        return session

    def remove_ingredient(
        self, session_id: str, ingredient_id: str
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.ingredients = [
            ing for ing in session.ingredients if ing.id != ingredient_id
        ]
        session.updated_at = datetime.utcnow()
        return session

    def update_status(
        self, session_id: str, status: Literal["in_progress", "confirmed", "used"]
    ) -> Optional[IngredientSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.status = status
        session.updated_at = datetime.utcnow()
        return session


# Singleton instance
session_store = SessionStore()
```

**Step 4: Update services __init__.py**

```python
# backend/app/services/__init__.py
from .ingredient_parser import IngredientParser
from .session_store import SessionStore, session_store

__all__ = ["IngredientParser", "SessionStore", "session_store"]
```

**Step 5: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_session_store.py -v
# Expected: 7 passed
```

**Step 6: Commit**

```bash
git add backend/app/services/ backend/tests/test_session_store.py
git commit -m "feat: add in-memory session store for ingredients"
```

---

### Task 5: API Endpoints

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/ingredients.py`
- Create: `backend/tests/test_api_ingredients.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_api_ingredients.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import Ingredient


client = TestClient(app)


class TestParseEndpoint:
    def test_parse_ingredients_success(self):
        mock_ingredients = [
            Ingredient(
                name="chicken breast",
                quantity="2",
                raw_input="2 chicken breasts",
                confidence=0.95,
            )
        ]

        with patch("app.routers.ingredients.parser.parse", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_ingredients

            response = client.post(
                "/api/ingredients/parse",
                json={"text": "2 chicken breasts"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["ingredients"]) == 1
            assert data["ingredients"][0]["name"] == "chicken breast"
            assert data["raw_input"] == "2 chicken breasts"


class TestSessionEndpoints:
    def test_create_session(self):
        response = client.post(
            "/api/ingredients/session",
            json={"user_id": "user_123"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["status"] == "in_progress"
        assert "id" in data

    def test_get_latest_session(self):
        # Create a session first
        create_response = client.post(
            "/api/ingredients/session",
            json={"user_id": "user_456"}
        )
        session_id = create_response.json()["id"]

        response = client.get("/api/ingredients/session/latest?user_id=user_456")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id

    def test_get_latest_session_not_found(self):
        response = client.get("/api/ingredients/session/latest?user_id=nonexistent")
        assert response.status_code == 404

    def test_update_session_add_ingredients(self):
        # Create session
        create_response = client.post(
            "/api/ingredients/session",
            json={"user_id": "user_789"}
        )
        session_id = create_response.json()["id"]

        # Add ingredients
        response = client.patch(
            f"/api/ingredients/session/{session_id}",
            json={
                "add_ingredients": [
                    {
                        "name": "tomatoes",
                        "quantity": "3",
                        "raw_input": "3 tomatoes",
                        "confidence": 0.9,
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "tomatoes"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_api_ingredients.py -v
# Expected: FAIL - 404 or import errors
```

**Step 3: Create routers directory**

```bash
mkdir -p backend/app/routers
touch backend/app/routers/__init__.py
```

**Step 4: Write the ingredients router**

```python
# backend/app/routers/ingredients.py
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import Ingredient, IngredientSession
from app.services import IngredientParser, session_store


router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])
parser = IngredientParser()


# Request/Response schemas
class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    ingredients: list[Ingredient]
    raw_input: str


class CreateSessionRequest(BaseModel):
    user_id: str


class UpdateSessionRequest(BaseModel):
    add_ingredients: Optional[list[dict]] = None
    remove_ingredient_ids: Optional[list[str]] = None
    status: Optional[str] = None


# Endpoints
@router.post("/parse", response_model=ParseResponse)
async def parse_ingredients(request: ParseRequest):
    ingredients = await parser.parse(request.text)
    return ParseResponse(ingredients=ingredients, raw_input=request.text)


@router.post("/session", response_model=IngredientSession, status_code=201)
async def create_session(request: CreateSessionRequest):
    session = session_store.create_session(request.user_id)
    return session


@router.get("/session/latest", response_model=IngredientSession)
async def get_latest_session(user_id: str = Query(...)):
    session = session_store.get_latest_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No session found for user")
    return session


@router.get("/session/{session_id}", response_model=IngredientSession)
async def get_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/session/{session_id}", response_model=IngredientSession)
async def update_session(session_id: str, request: UpdateSessionRequest):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.add_ingredients:
        ingredients = [
            Ingredient(**ing) for ing in request.add_ingredients
        ]
        session_store.add_ingredients(session_id, ingredients)

    if request.remove_ingredient_ids:
        for ing_id in request.remove_ingredient_ids:
            session_store.remove_ingredient(session_id, ing_id)

    if request.status:
        session_store.update_status(session_id, request.status)

    return session_store.get_session(session_id)
```

**Step 5: Update main.py to include router**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ingredients

app = FastAPI(title="KondateAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingredients.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 6: Export router from __init__.py**

```python
# backend/app/routers/__init__.py
from . import ingredients

__all__ = ["ingredients"]
```

**Step 7: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_api_ingredients.py -v
# Expected: 5 passed
```

**Step 8: Commit**

```bash
git add backend/app/routers/ backend/app/main.py backend/tests/test_api_ingredients.py
git commit -m "feat: add ingredient parsing and session API endpoints"
```

---

## Phase 2: Frontend Foundation

### Task 6: Project Setup - Frontend

**Files:**
- Create: `frontend/` (Vite React TypeScript project)
- Create: `frontend/.env.example`

**Step 1: Create Vite project**

```bash
cd /Users/matthew/development/KondateAgent/.worktrees/ingredient-collection
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 2: Install dependencies**

```bash
cd frontend
npm install tailwindcss postcss autoprefixer
npm install @tanstack/react-query axios
npm install -D @types/node
npx tailwindcss init -p
```

**Step 3: Configure Tailwind**

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 4: Update CSS**

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 5: Create .env.example**

```bash
VITE_API_BASE_URL=http://localhost:8000
```

**Step 6: Create API client**

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**Step 7: Verify setup**

```bash
cd frontend
npm run dev &
sleep 3
curl http://localhost:5173 | head -20
# Expected: HTML response
pkill -f vite
```

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: initialize frontend with Vite, React, TypeScript, Tailwind"
```

---

### Task 7: TypeScript Types

**Files:**
- Create: `frontend/src/types/ingredient.ts`

**Step 1: Create types directory**

```bash
mkdir -p frontend/src/types
```

**Step 2: Write type definitions**

```typescript
// frontend/src/types/ingredient.ts
export interface Ingredient {
  id: string;
  name: string;
  quantity: string;
  unit?: string;
  raw_input: string;
  confidence: number;
  created_at: string;
}

export interface IngredientSession {
  id: string;
  user_id: string;
  ingredients: Ingredient[];
  created_at: string;
  updated_at: string;
  status: 'in_progress' | 'confirmed' | 'used';
}

export interface ParseResponse {
  ingredients: Ingredient[];
  raw_input: string;
}
```

**Step 3: Create index export**

```typescript
// frontend/src/types/index.ts
export * from './ingredient';
```

**Step 4: Commit**

```bash
git add frontend/src/types/
git commit -m "feat: add TypeScript types for ingredients"
```

---

### Task 8: API Hooks

**Files:**
- Create: `frontend/src/api/ingredients.ts`
- Create: `frontend/src/api/index.ts`

**Step 1: Create ingredients API**

```typescript
// frontend/src/api/ingredients.ts
import { apiClient } from './client';
import type { Ingredient, IngredientSession, ParseResponse } from '../types';

export const ingredientsApi = {
  parse: async (text: string): Promise<ParseResponse> => {
    const response = await apiClient.post('/api/ingredients/parse', { text });
    return response.data;
  },

  createSession: async (userId: string): Promise<IngredientSession> => {
    const response = await apiClient.post('/api/ingredients/session', { user_id: userId });
    return response.data;
  },

  getLatestSession: async (userId: string): Promise<IngredientSession | null> => {
    try {
      const response = await apiClient.get('/api/ingredients/session/latest', {
        params: { user_id: userId },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  getSession: async (sessionId: string): Promise<IngredientSession> => {
    const response = await apiClient.get(`/api/ingredients/session/${sessionId}`);
    return response.data;
  },

  addIngredients: async (
    sessionId: string,
    ingredients: Omit<Ingredient, 'id' | 'created_at'>[]
  ): Promise<IngredientSession> => {
    const response = await apiClient.patch(`/api/ingredients/session/${sessionId}`, {
      add_ingredients: ingredients,
    });
    return response.data;
  },

  removeIngredient: async (sessionId: string, ingredientId: string): Promise<IngredientSession> => {
    const response = await apiClient.patch(`/api/ingredients/session/${sessionId}`, {
      remove_ingredient_ids: [ingredientId],
    });
    return response.data;
  },

  updateStatus: async (
    sessionId: string,
    status: 'in_progress' | 'confirmed' | 'used'
  ): Promise<IngredientSession> => {
    const response = await apiClient.patch(`/api/ingredients/session/${sessionId}`, {
      status,
    });
    return response.data;
  },
};
```

**Step 2: Create index export**

```typescript
// frontend/src/api/index.ts
export { apiClient } from './client';
export { ingredientsApi } from './ingredients';
```

**Step 3: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add ingredients API client"
```

---

### Task 9: Voice Input Hook

**Files:**
- Create: `frontend/src/hooks/useVoiceInput.ts`
- Create: `frontend/src/hooks/index.ts`

**Step 1: Create hooks directory**

```bash
mkdir -p frontend/src/hooks
```

**Step 2: Write the voice input hook**

```typescript
// frontend/src/hooks/useVoiceInput.ts
import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceInputOptions {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  wakeWords?: string[];
}

interface UseVoiceInputReturn {
  isListening: boolean;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
}

export function useVoiceInput({
  onTranscript,
  onError,
  wakeWords = ['done', "that's it", 'that is it', 'finished'],
}: UseVoiceInputOptions): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const accumulatedTextRef = useRef<string>('');

  const isSupported = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      // Check for wake words to stop
      const lowerTranscript = transcript.toLowerCase();
      for (const word of wakeWords) {
        if (lowerTranscript.includes(word)) {
          recognition.stop();
          // Remove wake word from transcript
          const cleanedTranscript = accumulatedTextRef.current.trim();
          if (cleanedTranscript) {
            onTranscript(cleanedTranscript);
          }
          accumulatedTextRef.current = '';
          return;
        }
      }

      // Accumulate final results
      if (event.results[event.resultIndex].isFinal) {
        accumulatedTextRef.current += transcript + ' ';
        onTranscript(accumulatedTextRef.current.trim());
      }
    };

    recognition.onerror = (event) => {
      const errorMessage = getErrorMessage(event.error);
      setError(errorMessage);
      setIsListening(false);
      onError?.(errorMessage);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, [isSupported, onTranscript, onError, wakeWords]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;

    setError(null);
    accumulatedTextRef.current = '';

    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error('Failed to start recognition:', err);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;

    recognitionRef.current.stop();

    const finalText = accumulatedTextRef.current.trim();
    if (finalText) {
      onTranscript(finalText);
    }
    accumulatedTextRef.current = '';
  }, [onTranscript]);

  return {
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
  };
}

function getErrorMessage(error: string): string {
  switch (error) {
    case 'not-allowed':
      return 'Microphone permission denied. Please allow microphone access.';
    case 'no-speech':
      return "I didn't hear anything. Try speaking again.";
    case 'audio-capture':
      return 'No microphone found. Please check your audio settings.';
    case 'network':
      return 'Network error. Please check your connection.';
    default:
      return `Speech recognition error: ${error}`;
  }
}

// Add type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
```

**Step 3: Create index export**

```typescript
// frontend/src/hooks/index.ts
export { useVoiceInput } from './useVoiceInput';
```

**Step 4: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useVoiceInput hook for Web Speech API"
```

---

### Task 10: IngredientItem Component

**Files:**
- Create: `frontend/src/components/IngredientItem.tsx`
- Create: `frontend/src/components/index.ts`

**Step 1: Create components directory**

```bash
mkdir -p frontend/src/components
```

**Step 2: Write IngredientItem component**

```tsx
// frontend/src/components/IngredientItem.tsx
import { useState } from 'react';
import type { Ingredient } from '../types';

interface IngredientItemProps {
  ingredient: Ingredient;
  onEdit: (id: string, name: string, quantity: string) => void;
  onDelete: (id: string) => void;
}

export function IngredientItem({ ingredient, onEdit, onDelete }: IngredientItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(ingredient.name);
  const [editQuantity, setEditQuantity] = useState(ingredient.quantity);

  const handleSave = () => {
    onEdit(ingredient.id, editName, editQuantity);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditName(ingredient.name);
    setEditQuantity(ingredient.quantity);
    setIsEditing(false);
  };

  const isLowConfidence = ingredient.confidence < 0.7;

  if (isEditing) {
    return (
      <div className="flex items-center gap-2 p-3 bg-white rounded-lg shadow-sm border">
        <input
          type="text"
          value={editQuantity}
          onChange={(e) => setEditQuantity(e.target.value)}
          className="w-16 px-2 py-1 border rounded text-sm"
          placeholder="Qty"
        />
        <input
          type="text"
          value={editName}
          onChange={(e) => setEditName(e.target.value)}
          className="flex-1 px-2 py-1 border rounded text-sm"
          placeholder="Ingredient"
        />
        <button
          onClick={handleSave}
          className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
        >
          Save
        </button>
        <button
          onClick={handleCancel}
          className="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div
      className={`flex items-center justify-between p-3 bg-white rounded-lg shadow-sm border ${
        isLowConfidence ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'
      }`}
    >
      <button
        onClick={() => setIsEditing(true)}
        className="flex-1 text-left flex items-center gap-2"
      >
        <span className="font-medium text-gray-600">{ingredient.quantity}</span>
        <span className="text-gray-900">{ingredient.name}</span>
        {isLowConfidence && (
          <span className="text-yellow-600 text-sm" title="Low confidence - tap to verify">
            ?
          </span>
        )}
      </button>
      <button
        onClick={() => onDelete(ingredient.id)}
        className="ml-2 p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
        aria-label="Delete ingredient"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
```

**Step 3: Create index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
```

**Step 4: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add IngredientItem component with edit/delete"
```

---

### Task 11: IngredientList Component

**Files:**
- Create: `frontend/src/components/IngredientList.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write IngredientList component**

```tsx
// frontend/src/components/IngredientList.tsx
import type { Ingredient } from '../types';
import { IngredientItem } from './IngredientItem';

interface IngredientListProps {
  ingredients: Ingredient[];
  onEdit: (id: string, name: string, quantity: string) => void;
  onDelete: (id: string) => void;
}

export function IngredientList({ ingredients, onEdit, onDelete }: IngredientListProps) {
  if (ingredients.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No ingredients yet.</p>
        <p className="text-sm mt-1">Start speaking to add items from your fridge.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {ingredients.map((ingredient) => (
        <IngredientItem
          key={ingredient.id}
          ingredient={ingredient}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
```

**Step 2: Update index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add IngredientList component"
```

---

### Task 12: VoiceInputController Component

**Files:**
- Create: `frontend/src/components/VoiceInputController.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write VoiceInputController component**

```tsx
// frontend/src/components/VoiceInputController.tsx
import { useVoiceInput } from '../hooks';

interface VoiceInputControllerProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function VoiceInputController({ onTranscript, disabled }: VoiceInputControllerProps) {
  const { isListening, isSupported, error, startListening, stopListening } = useVoiceInput({
    onTranscript,
  });

  if (!isSupported) {
    return (
      <div className="text-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800">
          Voice input is not supported in your browser.
        </p>
        <p className="text-sm text-yellow-600 mt-1">
          Please use the text input below instead.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={isListening ? stopListening : startListening}
        disabled={disabled}
        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
          isListening
            ? 'bg-red-500 hover:bg-red-600 animate-pulse'
            : 'bg-blue-500 hover:bg-blue-600'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={isListening ? 'Stop listening' : 'Start listening'}
      >
        <svg
          className="w-8 h-8 text-white"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          {isListening ? (
            <rect x="6" y="6" width="12" height="12" rx="2" />
          ) : (
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z" />
          )}
        </svg>
      </button>

      <p className="text-sm text-gray-600">
        {isListening ? (
          <span className="text-red-600 font-medium">
            Listening... Say "done" when finished
          </span>
        ) : (
          'Tap to start speaking'
        )}
      </p>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
          {error}
        </p>
      )}
    </div>
  );
}
```

**Step 2: Update index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
export { VoiceInputController } from './VoiceInputController';
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add VoiceInputController component"
```

---

### Task 13: TextInputFallback Component

**Files:**
- Create: `frontend/src/components/TextInputFallback.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write TextInputFallback component**

```tsx
// frontend/src/components/TextInputFallback.tsx
import { useState } from 'react';

interface TextInputFallbackProps {
  onSubmit: (text: string) => void;
  isLoading?: boolean;
}

export function TextInputFallback({ onSubmit, isLoading }: TextInputFallbackProps) {
  const [text, setText] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSubmit(text.trim());
      setText('');
    }
  };

  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className="text-sm text-blue-600 hover:text-blue-800 underline"
      >
        Type instead
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your ingredients..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Adding...' : 'Add'}
        </button>
      </div>
      <button
        type="button"
        onClick={() => setIsExpanded(false)}
        className="mt-2 text-sm text-gray-500 hover:text-gray-700"
      >
        Use voice instead
      </button>
    </form>
  );
}
```

**Step 2: Update index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
export { VoiceInputController } from './VoiceInputController';
export { TextInputFallback } from './TextInputFallback';
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add TextInputFallback component"
```

---

### Task 14: ConfirmationFooter Component

**Files:**
- Create: `frontend/src/components/ConfirmationFooter.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write ConfirmationFooter component**

```tsx
// frontend/src/components/ConfirmationFooter.tsx
interface ConfirmationFooterProps {
  ingredientCount: number;
  onConfirm: () => void;
  isLoading?: boolean;
}

export function ConfirmationFooter({
  ingredientCount,
  onConfirm,
  isLoading,
}: ConfirmationFooterProps) {
  const isDisabled = ingredientCount === 0 || isLoading;

  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 shadow-lg">
      <button
        onClick={onConfirm}
        disabled={isDisabled}
        className={`w-full py-4 rounded-lg text-lg font-semibold transition-all ${
          isDisabled
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-green-500 text-white hover:bg-green-600 active:bg-green-700'
        }`}
      >
        {isLoading ? (
          'Processing...'
        ) : ingredientCount === 0 ? (
          'Add ingredients to continue'
        ) : (
          `Looks good, plan my meals! (${ingredientCount} items)`
        )}
      </button>
    </div>
  );
}
```

**Step 2: Update index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
export { VoiceInputController } from './VoiceInputController';
export { TextInputFallback } from './TextInputFallback';
export { ConfirmationFooter } from './ConfirmationFooter';
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add ConfirmationFooter component"
```

---

### Task 15: SessionStartModal Component

**Files:**
- Create: `frontend/src/components/SessionStartModal.tsx`
- Modify: `frontend/src/components/index.ts`

**Step 1: Write SessionStartModal component**

```tsx
// frontend/src/components/SessionStartModal.tsx
interface SessionStartModalProps {
  hasExistingSession: boolean;
  existingIngredientCount: number;
  onStartFresh: () => void;
  onUpdateExisting: () => void;
}

export function SessionStartModal({
  hasExistingSession,
  existingIngredientCount,
  onStartFresh,
  onUpdateExisting,
}: SessionStartModalProps) {
  if (!hasExistingSession) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          Welcome back!
        </h2>
        <p className="text-gray-600 mb-6">
          You have {existingIngredientCount} ingredient{existingIngredientCount !== 1 ? 's' : ''} from your last session.
        </p>

        <div className="space-y-3">
          <button
            onClick={onUpdateExisting}
            className="w-full py-3 px-4 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
          >
            Update my last list
          </button>
          <button
            onClick={onStartFresh}
            className="w-full py-3 px-4 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Start fresh
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Update index export**

```typescript
// frontend/src/components/index.ts
export { IngredientItem } from './IngredientItem';
export { IngredientList } from './IngredientList';
export { VoiceInputController } from './VoiceInputController';
export { TextInputFallback } from './TextInputFallback';
export { ConfirmationFooter } from './ConfirmationFooter';
export { SessionStartModal } from './SessionStartModal';
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add SessionStartModal component"
```

---

## Phase 3: Integration

### Task 16: IngredientCollectionPage

**Files:**
- Create: `frontend/src/pages/IngredientCollectionPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write the main page component**

```tsx
// frontend/src/pages/IngredientCollectionPage.tsx
import { useState, useEffect, useCallback } from 'react';
import {
  IngredientList,
  VoiceInputController,
  TextInputFallback,
  ConfirmationFooter,
  SessionStartModal,
} from '../components';
import { ingredientsApi } from '../api';
import type { Ingredient, IngredientSession } from '../types';

// Temporary user ID - replace with auth later
const USER_ID = 'demo_user';

export function IngredientCollectionPage() {
  const [session, setSession] = useState<IngredientSession | null>(null);
  const [showStartModal, setShowStartModal] = useState(false);
  const [existingSession, setExistingSession] = useState<IngredientSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const checkExistingSession = async () => {
      try {
        const latest = await ingredientsApi.getLatestSession(USER_ID);
        if (latest && latest.status === 'in_progress') {
          setExistingSession(latest);
          setShowStartModal(true);
        } else {
          // No existing session, create new one
          const newSession = await ingredientsApi.createSession(USER_ID);
          setSession(newSession);
        }
      } catch (error) {
        console.error('Failed to check existing session:', error);
        // Create new session on error
        const newSession = await ingredientsApi.createSession(USER_ID);
        setSession(newSession);
      }
    };

    checkExistingSession();
  }, []);

  const handleStartFresh = async () => {
    const newSession = await ingredientsApi.createSession(USER_ID);
    setSession(newSession);
    setShowStartModal(false);
  };

  const handleUpdateExisting = () => {
    setSession(existingSession);
    setShowStartModal(false);
  };

  const handleTranscript = useCallback(async (text: string) => {
    if (!session || !text.trim()) return;

    setIsParsing(true);
    try {
      const parsed = await ingredientsApi.parse(text);
      if (parsed.ingredients.length > 0) {
        const updatedSession = await ingredientsApi.addIngredients(
          session.id,
          parsed.ingredients.map((ing) => ({
            name: ing.name,
            quantity: ing.quantity,
            unit: ing.unit,
            raw_input: ing.raw_input,
            confidence: ing.confidence,
          }))
        );
        setSession(updatedSession);
      }
    } catch (error) {
      console.error('Failed to parse ingredients:', error);
    } finally {
      setIsParsing(false);
    }
  }, [session]);

  const handleEdit = useCallback(async (id: string, name: string, quantity: string) => {
    if (!session) return;

    // For simplicity, we remove and re-add. In production, add an update endpoint.
    const ingredient = session.ingredients.find((ing) => ing.id === id);
    if (!ingredient) return;

    try {
      await ingredientsApi.removeIngredient(session.id, id);
      const updatedSession = await ingredientsApi.addIngredients(session.id, [
        {
          name,
          quantity,
          unit: ingredient.unit,
          raw_input: ingredient.raw_input,
          confidence: 1.0, // User verified
        },
      ]);
      setSession(updatedSession);
    } catch (error) {
      console.error('Failed to edit ingredient:', error);
    }
  }, [session]);

  const handleDelete = useCallback(async (id: string) => {
    if (!session) return;

    try {
      const updatedSession = await ingredientsApi.removeIngredient(session.id, id);
      setSession(updatedSession);
    } catch (error) {
      console.error('Failed to delete ingredient:', error);
    }
  }, [session]);

  const handleConfirm = async () => {
    if (!session) return;

    setIsLoading(true);
    try {
      await ingredientsApi.updateStatus(session.id, 'confirmed');
      // Navigate to meal planning (implement routing later)
      alert('Session confirmed! Redirecting to meal planning...');
    } catch (error) {
      console.error('Failed to confirm session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      <SessionStartModal
        hasExistingSession={showStartModal}
        existingIngredientCount={existingSession?.ingredients.length ?? 0}
        onStartFresh={handleStartFresh}
        onUpdateExisting={handleUpdateExisting}
      />

      <header className="bg-white shadow-sm p-4">
        <h1 className="text-xl font-bold text-gray-900">
          What's in your fridge?
        </h1>
        <p className="text-sm text-gray-600">
          Tell me what ingredients you have
        </p>
      </header>

      <main className="p-4 space-y-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <VoiceInputController
            onTranscript={handleTranscript}
            disabled={isParsing}
          />

          <div className="mt-4 flex justify-center">
            <TextInputFallback
              onSubmit={handleTranscript}
              isLoading={isParsing}
            />
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Your ingredients
          </h2>
          <IngredientList
            ingredients={session?.ingredients ?? []}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </div>
      </main>

      <ConfirmationFooter
        ingredientCount={session?.ingredients.length ?? 0}
        onConfirm={handleConfirm}
        isLoading={isLoading}
      />
    </div>
  );
}
```

**Step 2: Update App.tsx**

```tsx
// frontend/src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IngredientCollectionPage } from './pages/IngredientCollectionPage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <IngredientCollectionPage />
    </QueryClientProvider>
  );
}

export default App;
```

**Step 3: Create pages index**

```typescript
// frontend/src/pages/index.ts
export { IngredientCollectionPage } from './IngredientCollectionPage';
```

**Step 4: Commit**

```bash
git add frontend/src/pages/ frontend/src/App.tsx
git commit -m "feat: add IngredientCollectionPage with full integration"
```

---

## Phase 4: Testing & Polish

### Task 17: Backend Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

**Step 1: Write integration test**

```python
# backend/tests/test_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import Ingredient


client = TestClient(app)


class TestFullFlow:
    """Test the complete ingredient collection flow."""

    def test_create_session_parse_add_confirm(self):
        # 1. Create session
        create_response = client.post(
            "/api/ingredients/session",
            json={"user_id": "integration_test_user"}
        )
        assert create_response.status_code == 201
        session = create_response.json()
        session_id = session["id"]

        # 2. Parse ingredients (mocked)
        mock_ingredients = [
            {"name": "chicken breast", "quantity": "2", "unit": "pieces", "confidence": 0.95},
            {"name": "broccoli", "quantity": "1", "unit": "head", "confidence": 0.9},
        ]

        with patch("app.routers.ingredients.parser.parse", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = [
                Ingredient(
                    name=ing["name"],
                    quantity=ing["quantity"],
                    unit=ing["unit"],
                    raw_input="2 chicken breasts and 1 head of broccoli",
                    confidence=ing["confidence"],
                )
                for ing in mock_ingredients
            ]

            parse_response = client.post(
                "/api/ingredients/parse",
                json={"text": "2 chicken breasts and 1 head of broccoli"}
            )
            assert parse_response.status_code == 200
            parsed = parse_response.json()
            assert len(parsed["ingredients"]) == 2

        # 3. Add parsed ingredients to session
        update_response = client.patch(
            f"/api/ingredients/session/{session_id}",
            json={
                "add_ingredients": [
                    {
                        "name": "chicken breast",
                        "quantity": "2",
                        "unit": "pieces",
                        "raw_input": "2 chicken breasts",
                        "confidence": 0.95,
                    },
                    {
                        "name": "broccoli",
                        "quantity": "1",
                        "unit": "head",
                        "raw_input": "1 head of broccoli",
                        "confidence": 0.9,
                    },
                ]
            }
        )
        assert update_response.status_code == 200
        updated_session = update_response.json()
        assert len(updated_session["ingredients"]) == 2

        # 4. Confirm session
        confirm_response = client.patch(
            f"/api/ingredients/session/{session_id}",
            json={"status": "confirmed"}
        )
        assert confirm_response.status_code == 200
        confirmed_session = confirm_response.json()
        assert confirmed_session["status"] == "confirmed"

        # 5. Verify latest session
        latest_response = client.get(
            "/api/ingredients/session/latest",
            params={"user_id": "integration_test_user"}
        )
        assert latest_response.status_code == 200
        latest = latest_response.json()
        assert latest["id"] == session_id
        assert latest["status"] == "confirmed"
```

**Step 2: Run integration test**

```bash
cd backend
pytest tests/test_integration.py -v
# Expected: 1 passed
```

**Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add backend integration test for full flow"
```

---

### Task 18: Run All Tests

**Step 1: Run all backend tests**

```bash
cd backend
pytest -v
# Expected: All tests pass
```

**Step 2: Verify frontend builds**

```bash
cd frontend
npm run build
# Expected: Build succeeds
```

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: verify all tests pass and frontend builds"
```

---

## Summary

**Completed:**
- Backend with FastAPI, Pydantic models, OpenAI integration
- In-memory session store for ingredients
- REST API endpoints for parse, session CRUD
- Frontend with React, TypeScript, TailwindCSS
- Voice input with Web Speech API
- Text fallback input
- Real-time ingredient list with edit/delete
- Session persistence (start fresh vs update)
- Confirmation flow

**Next Steps (not in this plan):**
- Add database persistence (PostgreSQL)
- Add user authentication
- Add routing for meal planning page
- Add E2E tests with Playwright
- Deploy to production
