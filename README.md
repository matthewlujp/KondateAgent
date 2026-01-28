# KondateAgent

A meal planning application that helps users create weekly meal plans based on ingredients in their refrigerator. The system gathers recipes from user-specified sources (YouTube, Instagram, etc.) and proposes efficient meal plans that minimize food waste and additional purchases.

## Features

- Interactive ingredient input (chat/voice)
- Multi-source recipe aggregation (YouTube, Instagram)
- AI-powered meal plan generation optimized for ingredient usage
- Interactive feedback and plan refinement
- Shopping list generation with checkbox support
- Mobile-first browser interface

## Technology Stack

- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript + Vite
- **AI**: OpenAI ChatGPT API
- **Platform**: Mobile-first web application

## Project Structure

```
.
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── models/      # Data models
│   │   ├── routers/     # API endpoints
│   │   └── services/    # Business logic
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   ├── src/
│   └── public/
└── README.md           # This file
```

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn

## Setup & Running

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys (OpenAI, YouTube, Instagram)
```

5. Start the backend server:
```bash
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (default Vite port)

## Development Commands

### Backend

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_ingredients.py

# Start dev server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Environment Variables

### Backend (.env)

```
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
INSTAGRAM_API_KEY=your_instagram_api_key  # Optional
```

### Frontend (.env)

```
VITE_API_BASE_URL=http://localhost:8000
```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /api/recipes` - Get recipe collection
- `POST /api/recipes/search` - Search recipes by ingredients
- `GET /api/creators` - Get configured recipe creators

For full API documentation, visit `http://localhost:8000/docs` when the backend is running.

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]
