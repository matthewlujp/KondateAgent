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

### Python Package Management
**IMPORTANT**: This project uses `uv` for Python package management. Always use `uv` commands:
- `uv add <package>` - Add a new dependency
- `uv sync` - Sync dependencies from lockfile
- `uv run <command>` - Run commands in the uv environment (e.g., `uv run pytest`)
- DO NOT use `pip install` or manual venv activation

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
# Sync dependencies (uv automatically manages the virtual environment)
uv sync

# Run backend server
uv run uvicorn app.main:app --reload

# Run tests (with parallel execution)
uv run pytest -n auto

# Run specific test
uv run pytest -n auto tests/test_recipe_search.py::test_youtube_integration

# Add a new dependency
uv add <package-name>
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



## Project Structure Philosophy

This project follows **Layered Specification-Driven Development**.

### Layer Hierarchy (CRITICAL - READ FIRST)
````
L0: specs/PRINCIPLES.md   → WHY we build
L1: specs/ARCHITECTURE.md → HOW we build (system-wide)
L2: specs/DOMAIN.md       → WHAT we build (conceptual)
L3: specs/features/*/SPEC.md   → WHICH features
L4: Docs/plans/*.md            → Implementation details
````

**Inheritance Rule**: Lower layers MUST reference and comply with upper layers.

---

## Mandatory Workflow

### Before ANY code change:

1. **Check Foundation Compliance**
````bash
   # Always verify against specs layers first
   - Read specs/ARCHITECTURE.md
   - Read specs/DOMAIN.md
   - Verify no conflicts
````

2. **Update Sequence (STRICT ORDER)**
````
   ❌ WRONG: specs/features/payment/SPEC.md → code (skipping foundation check)
   ✅ RIGHT: specs/* → specs/features/*/SPEC.md → code
````

### When Creating New Features
````markdown
## Step 1: Foundation Check (MANDATORY)
- [ ] Read specs/ARCHITECTURE.md
- [ ] Read specs/DOMAIN.md
- [ ] Identify inherited constraints
- [ ] List in SPEC.md under "## Inherited Constraints"

## Step 2: Create Feature SPEC
Location: specs/features/<feature-name>/SPEC.md

Template:
```yaml
---
inherits_from:
  - ../../specs/ARCHITECTURE.md#<section>
  - ../../specs/DOMAIN.md#<entity>
validation_mode: strict
---

# Feature: <Name>

## Inherited Constraints
[Auto-populate from foundation layers]

## Feature-Specific Requirements
[Only add what's unique to this feature]
```

## Step 3: Validate Consistency
Before implementation:
- Run: /validate-layer-consistency
- Fix any conflicts with foundation
- Get approval if foundation change needed
````

---

## Architecture Change Protocol

### Changing specs/ARCHITECTURE.md

⚠️ **HIGH IMPACT - Special Process Required**
````markdown
1. Create RFC document:
   specs/rfcs/YYYYMMDD-<change>.md

2. Impact Analysis:
   - List all affected features
   - Estimate migration effort
   - Identify breaking changes

3. Approval Required:
   - Tech Lead: [ ]
   - Product: [ ]
   - Security (if auth/data): [ ]

4. Migration Plan:
   - Update specs/ARCHITECTURE.md
   - Update all specs/features/*/SPEC.md
   - Update all Docs/plans/*.md
   - Run full test suite
````

### Changing specs/DOMAIN.md

⚠️ **MEDIUM IMPACT**
````markdown
1. Check feature dependencies:
   grep -r "specs/DOMAIN.md" specs/features/

2. Update all dependent features

3. Approval Required:
   - Domain Expert: [ ]
   - Lead Developer: [ ]
````

---

## Code Generation Rules

### ALWAYS check foundation first
````typescript
// ❌ WRONG
async function createPayment(userId: string, amount: number) {
  // Direct implementation without checking ARCHITECTURE.md
}

// ✅ RIGHT - References foundation
/**
 * Payment creation following:
 * - ARCHITECTURE.md#database-strategy (PostgreSQL)
 * - ARCHITECTURE.md#transaction-guarantee (ACID)
 * - DOMAIN.md#payment-entity
 */
async function createPayment(userId: string, amount: number) {
  // Implementation that respects foundation constraints
}
````

---

## Consistency Validation

### Before committing code:
````bash
# Run these checks (implement as git hooks)

1. Check spec references:
   - All features reference foundation
   - No orphaned constraints
   
2. Check inheritance:
   - Features don't contradict foundation
   - Database choices match ARCHITECTURE.md
   - Entity definitions match DOMAIN.md

3. Check completeness:
   - All foundation changes propagated
   - No stale references
````

---

## Common Patterns

### Pattern 1: Adding a new feature
````bash
1. Read specs/ARCHITECTURE.md
2. Read specs/DOMAIN.md
3. Create specs/features/new-feature/SPEC.md
4. Reference foundation constraints explicitly
5. Add only feature-specific details
6. Generate PLAN.md from SPEC.md
````

### Pattern 2: Modifying architecture
````bash
1. Create specs/rfcs/change-proposal.md
2. Run impact analysis across all features
3. Get approvals
4. Update specs/ARCHITECTURE.md
5. Update ALL affected specs/features/*/SPEC.md
6. Verify with /validate-layer-consistency
````

### Pattern 3: Refactoring domain model
````bash
1. Identify affected entities in DOMAIN.md
2. Find all features using those entities
3. Update DOMAIN.md first
4. Cascade updates to features
5. Update implementation
````

---

## RED FLAGS - Stop Immediately If You See:

❌ **Feature SPEC without foundation references**
❌ **Direct implementation without checking ARCHITECTURE.md**
❌ **Database choice in feature that differs from ARCHITECTURE.md**
❌ **Entity definition in feature that differs from DOMAIN.md**
❌ **Multiple features defining the same constraint differently**

---

## Success Metrics

✅ **Good State**:
- All features reference foundation
- specs/ changes tracked in git history
- Impact analysis before architectural changes
- No redundant constraint definitions

❌ **Bad State**:
- Features with contradicting database choices
- No clear inheritance chain
- Foundation changes without feature updates
- Stale references

---

## Example: Full Workflow

### Scenario: Add "Payment Processing" feature
````markdown
1. Foundation Check:
   Read: specs/ARCHITECTURE.md
   - Database: PostgreSQL ✓
   - Auth: Auth0 ✓
   - API: RESTful ✓
   
   Read: specs/DOMAIN.md
   - User entity exists ✓
   - Payment entity defined ✓

2. Create Spec:
   File: specs/features/payment-processing/SPEC.md
```yaml
   ---
   inherits_from:
     - ../../specs/ARCHITECTURE.md#database-strategy
     - ../../specs/ARCHITECTURE.md#api-design
     - ../../specs/DOMAIN.md#payment
     - ../../specs/DOMAIN.md#user
   ---
   
   # Payment Processing
   
   ## Inherited Constraints
   - Database: PostgreSQL (ARCHITECTURE.md)
   - ACID transactions required (ARCHITECTURE.md)
   - RESTful API (ARCHITECTURE.md)
   - Payment entity schema (DOMAIN.md)
   
   ## Feature-Specific
   - Stripe integration
   - Webhook handling
   - Idempotency keys
```

3. Generate Plan:
   Creates PLAN.md based on SPEC.md

4. Implement:
   Code respects all inherited constraints

5. Validate:
   /validate-layer-consistency
   → ✓ All layers aligned
````

---

## Troubleshooting

### "Feature spec conflicts with architecture"
````bash
1. Check which constraint conflicts
2. Decide:
   - Option A: Update feature to match architecture
   - Option B: Update architecture (requires RFC)
3. Never: Ignore the conflict
````

### "Architecture change broke multiple features"
````bash
1. Run: /impact-analysis specs/ARCHITECTURE.md "<change>"
2. Review all affected features
3. Create migration checklist
4. Update features one by one
5. Run tests after each update
````

---

## Philosophy

> **Foundation layers (L0-L2) change slowly and deliberately.**
> **Feature layers (L3-L4) change frequently but within foundation constraints.**
> 
> This creates **stability at the core, flexibility at the edges**.

When in doubt, ask:
- "Does this contradict foundation?"
- "Should this be in foundation or feature?"
- "Have I checked all inheritance?"

---

## Quick Reference Card

| Task | Check | Update Order |
|------|-------|--------------|
| New feature | specs/* | foundation → feature SPEC → code |
| Change arch | Impact analysis | RFC → foundation → all features → code |
| Refactor domain | Feature dependencies | DOMAIN.md → feature SPECs → code |
| Bug fix | Feature SPEC only | feature SPEC → code |

---

Remember: **Consistency is more valuable than speed.**
Take time to maintain the layer hierarchy - it prevents future breakage.