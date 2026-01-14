# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KondateAgent is a meal planning application that helps users create weekly meal plans based on ingredients in their refrigerator. The system gathers recipes from user-specified sources (YouTube, Instagram, etc.) and proposes efficient meal plans that minimize food waste and additional purchases.

### Core Features
- Interactive ingredient input (chat/voice)
- Multi-source recipe aggregation
- AI-powered meal plan generation optimized for ingredient usage
- Interactive feedback and plan refinement
- Shopping list generation with checkbox support
- Mobile-first browser interface

### Technology Stack
- **Backend**: Python with LangGraph for AI workflow orchestration
- **Frontend**: React + Vite
- **AI**: ChatGPT API (OpenAI)
- **Target Platform**: Mobile-first web application

## Project Architecture

### Backend (Python)
The backend uses LangGraph to orchestrate the meal planning workflow as a state machine:

1. **Ingredient Collection Node**: Processes user input about refrigerator contents
2. **Recipe Search Node**: Queries multiple sources (YouTube, Instagram) based on user configuration
3. **Meal Plan Generation Node**: Uses ChatGPT API to create optimized weekly meal plans
4. **Feedback Processing Node**: Handles user feedback and triggers re-planning
5. **Shopping List Node**: Generates final ingredient shopping lists

Key considerations:
- LangGraph state should maintain: current ingredients, recipe candidates, current meal plan, user preferences/feedback
- Recipe sources are user-configurable and extensible
- The system prioritizes ingredient efficiency over exact recipe measurements
- Each recipe must include: link, thumbnail, ingredient list

### Frontend (React + Vite)
Mobile-first responsive design with these key views:

1. **Ingredient Input**: Chat/voice interface for listing refrigerator contents
2. **Meal Plan Display**: Weekly view showing proposed dishes with thumbnails, links, and ingredients
3. **Feedback Interface**: Quick actions ("looks good", "don't like", "not in the mood")
4. **Shopping List**: Checkable list of missing ingredients

Design principles:
- Touch-friendly UI for mobile
- Fast loading and responsive interactions
- Progressive enhancement for voice/image features

### API Integration
- OpenAI ChatGPT API for natural language understanding and meal plan generation
- YouTube Data API for video recipe metadata
- Instagram Graph API (or web scraping fallback) for recipe posts
- Consider rate limiting and caching strategies for external APIs

## Development Commands

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
python -m uvicorn app.main:app --reload

# Run tests
pytest

# Run specific test
pytest tests/test_recipe_search.py::test_youtube_integration
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run specific test
npm test -- RecipeCard.test.jsx
```

## Key Implementation Notes

### LangGraph Workflow Design
The meal planning workflow should be implemented as a cyclical graph allowing iterative refinement:
- Use conditional edges to handle user feedback loops
- Maintain conversation history for context-aware replanning
- Implement checkpoints for resuming interrupted sessions

### Recipe Matching Algorithm
The core challenge is matching available ingredients to recipes efficiently:
- Use embeddings or keyword matching to find recipes using existing ingredients
- Calculate a "coverage score" (percentage of ingredients already available)
- Sort candidates by coverage score and ingredient overlap
- Consider ingredient substitutability (e.g., chicken breast vs. chicken thigh)

### Shopping List Optimization
Generate minimal shopping lists by:
- Tracking which recipes share common ingredients
- Prioritizing recipes that require fewer new purchases
- Grouping ingredients by category (produce, protein, pantry, etc.)

### User Management
Keep authentication simple initially:
- Email/password registration and login
- JWT tokens for session management
- Store user preferences (favorite sources, dietary restrictions)

### Future Features (Not Initial Priority)
- Voice input integration (Web Speech API)
- Image recognition for ingredient photos (OpenAI Vision API or custom model)
- Meal prep scheduling and notifications
- Nutritional information tracking

## Configuration

### Environment Variables
Create `.env` files for both backend and frontend:

Backend `.env`:
```
OPENAI_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
DATABASE_URL=postgresql://...
SECRET_KEY=your_secret_key
```

Frontend `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

### Recipe Sources Configuration
Users should be able to configure sources via UI. Store in user profile:
```json
{
  "recipe_sources": [
    {"type": "youtube", "channel_id": "UCxxxx"},
    {"type": "instagram", "account": "foodblogger"}
  ]
}
```

## Testing Strategy

### Backend Tests
- Unit tests for LangGraph nodes (ingredient parsing, recipe matching, plan generation)
- Integration tests for external API calls (mock responses)
- End-to-end tests for complete workflow cycles

### Frontend Tests
- Component tests for UI elements (React Testing Library)
- Integration tests for API communication
- Mobile responsiveness tests (viewport testing)

## Common Gotchas

1. **LangGraph State Management**: Ensure state is properly serialized between nodes. Use Pydantic models for type safety.

2. **API Rate Limits**: YouTube and Instagram APIs have rate limits. Implement caching and consider batch requests.

3. **Recipe Data Quality**: External sources may have inconsistent data. Build robust parsers with fallbacks.

4. **Mobile Viewport**: Test on actual devices, not just browser DevTools. Touch targets should be at least 44x44px.

5. **Ingredient Normalization**: "1 tomato" vs "tomatoes" vs "cherry tomatoes" - implement fuzzy matching and standardization.

6. **ChatGPT API Costs**: Monitor token usage. Optimize prompts to be concise while maintaining quality.
