# LangGraph Research for KondateAgent

> Comprehensive research on LangGraph framework and its application to the KondateAgent meal planning system.
>
> **Research Date**: January 2026
> **LangGraph Version**: Latest (0.2+)

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [LangGraph Overview](#langgraph-overview)
3. [Core Concepts](#core-concepts)
4. [State Management](#state-management)
5. [Graph Structure: Nodes and Edges](#graph-structure-nodes-and-edges)
6. [Persistence and Checkpointing](#persistence-and-checkpointing)
7. [Human-in-the-Loop Workflows](#human-in-the-loop-workflows)
8. [Streaming and Real-Time Features](#streaming-and-real-time-features)
9. [Multi-Agent Orchestration](#multi-agent-orchestration)
10. [OpenAI/ChatGPT Integration](#openaichatgpt-integration)
11. [Production Deployment](#production-deployment)
12. [Application to KondateAgent](#application-to-kondateagent)
13. [Recommended Architecture](#recommended-architecture)
14. [Implementation Roadmap](#implementation-roadmap)
15. [References](#references)

---

## Executive Summary

LangGraph is the recommended framework for building the KondateAgent meal planning workflow. It provides:

- **Graph-based workflow orchestration** for managing complex meal planning states
- **Cyclic workflows** enabling iterative feedback loops for meal plan refinement
- **Built-in persistence** for resumable sessions and user history
- **Human-in-the-loop support** for user feedback integration
- **OpenAI integration** via LangChain's ChatOpenAI
- **Streaming capabilities** for real-time UI updates
- **Production-ready** architecture with FastAPI integration

LangGraph is trusted by companies like Klarna, Replit, and Elastic, with 600-800 companies expected in production by end of 2025.

---

## LangGraph Overview

### What is LangGraph?

LangGraph is a **low-level orchestration framework** for building long-running, stateful AI agents and workflows. It is built by LangChain Inc. but can be used independently of LangChain.

Key characteristics:
- **Graph-based architecture**: Organizes actions as nodes in a directed graph
- **State machine implementation**: Explicit control over workflow execution
- **Cyclic workflow support**: Unlike traditional DAGs, supports loops and iterative refinement
- **MIT licensed**: Free and open-source

### Why LangGraph for KondateAgent?

| Requirement | LangGraph Capability |
|-------------|---------------------|
| Multi-step meal planning workflow | Graph-based node orchestration |
| User feedback loops | Cyclic graphs with conditional edges |
| Session persistence | Built-in checkpointing system |
| ChatGPT integration | Native OpenAI support via LangChain |
| Real-time updates | Multiple streaming modes |
| Production deployment | FastAPI integration patterns |

### Installation

```bash
# Core installation
pip install langgraph langchain langchain-openai

# Persistence backends
pip install langgraph-checkpoint-sqlite  # For development
pip install langgraph-checkpoint-postgres  # For production

# API framework
pip install fastapi uvicorn python-dotenv
```

---

## Core Concepts

### Building Blocks

LangGraph operates on three fundamental components:

1. **Nodes**: Individual actions or tasks (LLM calls, tool executions, functions)
2. **Edges**: Connections defining workflow sequence and logic
3. **State**: Data retained between steps for context preservation

### Graph Types

```python
from langgraph.graph import StateGraph, START, END

# StateGraph accepts a state schema and manages state throughout execution
builder = StateGraph(MyState)
builder.add_node("node_name", node_function)
builder.add_edge(START, "node_name")
builder.add_edge("node_name", END)

# Compile to create executable graph
graph = builder.compile()
```

### Execution Methods

- `graph.invoke(input)` - Synchronous execution
- `graph.ainvoke(input)` - Async execution
- `graph.stream(input)` - Streaming execution
- `graph.astream(input)` - Async streaming

---

## State Management

### State Schema with TypedDict

TypedDict is the recommended approach for defining state schemas:

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import operator

class MealPlanState(TypedDict):
    """State for the meal planning workflow."""
    # User inputs
    ingredients: List[str]
    dietary_restrictions: List[str]

    # Recipe data
    recipe_candidates: List[dict]

    # Generated plan
    current_meal_plan: dict

    # Conversation
    messages: Annotated[List[AnyMessage], add_messages]

    # Feedback loop
    user_feedback: str
    iteration_count: int

    # Accumulating lists use reducer functions
    shopping_list: Annotated[List[str], operator.add]
```

### Reducers for State Updates

Reducers control how state updates are merged:

```python
from typing import Annotated
import operator

class State(TypedDict):
    # Replaces value on each update
    current_plan: dict

    # Appends to list on each update
    all_suggestions: Annotated[List[str], operator.add]

    # Custom message merging
    messages: Annotated[List[AnyMessage], add_messages]
```

### Pydantic BaseModel for Validation

For stricter type checking and validation:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

class Recipe(BaseModel):
    title: str
    url: str
    thumbnail: Optional[str] = None
    ingredients: List[Ingredient]
    coverage_score: float = Field(ge=0, le=1)

class MealPlanState(BaseModel):
    """Validated state schema for meal planning."""
    ingredients: List[Ingredient] = []
    recipes: List[Recipe] = []
    current_plan: Optional[dict] = None
    feedback: Optional[str] = None
```

> **Note**: Pydantic validation only runs on inputs to the first node. For performance-sensitive applications, TypedDict may be preferred.

---

## Graph Structure: Nodes and Edges

### Defining Nodes

Nodes are functions that receive state and return state updates:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def ingredient_parser_node(state: MealPlanState) -> dict:
    """Parse user input to extract ingredients."""
    messages = state["messages"]

    response = llm.invoke([
        SystemMessage(content="Extract ingredients from user input..."),
        *messages
    ])

    # Return partial state update
    return {
        "ingredients": parse_ingredients(response.content),
        "messages": [response]
    }

def recipe_search_node(state: MealPlanState) -> dict:
    """Search for recipes matching ingredients."""
    ingredients = state["ingredients"]

    # Call YouTube/Instagram APIs
    recipes = search_recipes(ingredients)

    return {"recipe_candidates": recipes}

def meal_plan_generator_node(state: MealPlanState) -> dict:
    """Generate optimized meal plan using ChatGPT."""
    recipes = state["recipe_candidates"]
    ingredients = state["ingredients"]
    feedback = state.get("user_feedback", "")

    prompt = build_meal_plan_prompt(recipes, ingredients, feedback)
    response = llm.invoke(prompt)

    return {
        "current_meal_plan": parse_meal_plan(response.content),
        "iteration_count": state.get("iteration_count", 0) + 1
    }
```

### Basic Edges

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(MealPlanState)

# Add nodes
builder.add_node("parse_ingredients", ingredient_parser_node)
builder.add_node("search_recipes", recipe_search_node)
builder.add_node("generate_plan", meal_plan_generator_node)

# Add edges (linear flow)
builder.add_edge(START, "parse_ingredients")
builder.add_edge("parse_ingredients", "search_recipes")
builder.add_edge("search_recipes", "generate_plan")
builder.add_edge("generate_plan", END)
```

### Conditional Edges

Conditional edges enable dynamic routing based on state:

```python
def route_after_feedback(state: MealPlanState) -> str:
    """Determine next step based on user feedback."""
    feedback = state.get("user_feedback", "")
    iteration = state.get("iteration_count", 0)

    if not feedback or feedback == "looks_good":
        return "shopping_list"
    elif feedback in ["dont_like", "not_in_mood"]:
        if iteration < 3:  # Max iterations
            return "generate_plan"
        else:
            return "shopping_list"
    else:
        return "generate_plan"

# Add conditional edge
builder.add_conditional_edges(
    "feedback_handler",
    route_after_feedback,
    {
        "generate_plan": "generate_plan",
        "shopping_list": "shopping_list_node"
    }
)
```

### Cyclic Graphs for Feedback Loops

LangGraph's key differentiator is support for cycles:

```python
builder = StateGraph(MealPlanState)

# Nodes
builder.add_node("generate_plan", meal_plan_generator_node)
builder.add_node("wait_feedback", feedback_collection_node)
builder.add_node("process_feedback", feedback_processor_node)
builder.add_node("create_shopping_list", shopping_list_node)

# Entry point
builder.add_edge(START, "generate_plan")

# Feedback loop
builder.add_edge("generate_plan", "wait_feedback")
builder.add_edge("wait_feedback", "process_feedback")

# Conditional routing creates the cycle
builder.add_conditional_edges(
    "process_feedback",
    route_after_feedback,
    {
        "regenerate": "generate_plan",  # Loop back
        "finalize": "create_shopping_list"  # Exit loop
    }
)

builder.add_edge("create_shopping_list", END)
```

---

## Persistence and Checkpointing

### Overview

LangGraph's persistence layer enables:
- **Session memory**: Store conversation history
- **Error recovery**: Resume from last successful step
- **Human-in-the-loop**: Pause and resume workflows
- **Time travel**: Access historical states

### Checkpointer Options

| Checkpointer | Use Case | Installation |
|-------------|----------|--------------|
| `MemorySaver` | Development/testing | Built-in |
| `SqliteSaver` | Local development | `pip install langgraph-checkpoint-sqlite` |
| `PostgresSaver` | Production | `pip install langgraph-checkpoint-postgres` |

### Using MemorySaver (Development)

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# Execute with thread_id for session tracking
config = {"configurable": {"thread_id": "user-123-session-1"}}
result = graph.invoke(input_state, config)

# Resume same session later
result = graph.invoke({"user_feedback": "don't like fish"}, config)
```

### Using SqliteSaver (Development with Persistence)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# In-memory (non-persistent)
memory = SqliteSaver.from_conn_string(":memory:")

# File-based (persistent)
memory = SqliteSaver.from_conn_string("checkpoints.sqlite")

graph = builder.compile(checkpointer=memory)
```

### Using PostgresSaver (Production)

```python
from langgraph.checkpoint.postgres import PostgresSaver
import os

DATABASE_URL = os.getenv("DATABASE_URL")

with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    result = graph.invoke(input_state, config)
```

### Async Checkpointers for FastAPI

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_checkpointer():
    return AsyncPostgresSaver.from_conn_string(DATABASE_URL)

# In FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.checkpointer = await get_checkpointer()
    yield
    await app.state.checkpointer.close()
```

### Accessing State History

```python
# Get current state
state_snapshot = graph.get_state(config)
print(state_snapshot.values)

# List all checkpoints
for checkpoint in graph.get_state_history(config):
    print(checkpoint.config, checkpoint.values)
```

---

## Human-in-the-Loop Workflows

### Why Human-in-the-Loop?

KondateAgent requires user feedback for meal plan refinement. LangGraph provides native HITL support through:

1. **Interrupts**: Pause execution at specific points
2. **State modification**: Allow users to modify state
3. **Resume**: Continue from interrupted state

### Static Interrupts

```python
# Compile with interrupt points
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["wait_feedback"],  # Pause before this node
    # interrupt_after=["generate_plan"]  # Or pause after
)

# First invocation - runs until interrupt
result = graph.invoke(initial_state, config)
# Graph pauses at "wait_feedback" node

# User provides feedback...

# Resume with Command
from langgraph.types import Command

graph.invoke(
    Command(resume={"user_feedback": "looks_good"}),
    config
)
```

### Dynamic Interrupts with `interrupt()`

```python
from langgraph.types import interrupt

def feedback_collection_node(state: MealPlanState) -> dict:
    """Wait for user feedback."""
    current_plan = state["current_meal_plan"]

    # Show plan to user and wait for response
    feedback = interrupt({
        "type": "feedback_request",
        "plan": current_plan,
        "options": ["looks_good", "dont_like", "not_in_mood", "customize"]
    })

    return {"user_feedback": feedback}
```

### Resuming After Interrupt

```python
from langgraph.types import Command

# Resume with user input
result = graph.invoke(
    Command(resume="looks_good"),
    config
)
```

---

## Streaming and Real-Time Features

### Streaming Modes

LangGraph supports multiple streaming modes for real-time UI updates:

| Mode | Description | Use Case |
|------|-------------|----------|
| `values` | Full state after each step | State monitoring |
| `updates` | State deltas only | Efficient state tracking |
| `messages` | LLM tokens + metadata | Chat-style interfaces |
| `custom` | User-defined data | Progress indicators |
| `debug` | Detailed traces | Debugging |

### Basic Streaming

```python
# Stream state updates
for event in graph.stream(input_state, config, stream_mode="updates"):
    print(f"Node: {event}")

# Stream multiple modes
for event in graph.stream(
    input_state,
    config,
    stream_mode=["updates", "messages"]
):
    print(event)
```

### Token Streaming for Chat UI

```python
from langchain_openai import ChatOpenAI

# Enable streaming on LLM
llm = ChatOpenAI(model="gpt-4o", streaming=True)

# Stream tokens using astream_events
async for event in graph.astream_events(input_state, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
            # Send to frontend via WebSocket/SSE
            await websocket.send(content)
```

### FastAPI Streaming Endpoint

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/meal-plan/stream")
async def stream_meal_plan(request: MealPlanRequest):
    async def generate():
        async for event in graph.astream_events(
            request.to_state(),
            {"configurable": {"thread_id": request.user_id}},
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## Multi-Agent Orchestration

### When to Use Multi-Agent

KondateAgent could benefit from multiple specialized agents:
- **Ingredient Parser Agent**: NLU for ingredient extraction
- **Recipe Search Agent**: Queries YouTube/Instagram APIs
- **Meal Planner Agent**: Optimizes weekly plans
- **Shopping List Agent**: Calculates missing ingredients

### Supervisor Pattern

```python
from langgraph_supervisor import create_supervisor

# Define specialized agents as tools
from langgraph.prebuilt import create_react_agent

ingredient_agent = create_react_agent(llm, [ingredient_parser_tool])
recipe_agent = create_react_agent(llm, [youtube_search, instagram_search])
planner_agent = create_react_agent(llm, [meal_optimizer_tool])

# Create supervisor
supervisor = create_supervisor(
    llm,
    agents=[ingredient_agent, recipe_agent, planner_agent],
    prompt="You are a meal planning coordinator..."
)
```

### Subgraphs for Modularity

```python
# Define recipe search as a subgraph
recipe_search_builder = StateGraph(RecipeSearchState)
recipe_search_builder.add_node("youtube", youtube_search_node)
recipe_search_builder.add_node("instagram", instagram_search_node)
recipe_search_builder.add_node("merge", merge_results_node)
recipe_search_graph = recipe_search_builder.compile()

# Use subgraph as node in main graph
main_builder = StateGraph(MealPlanState)
main_builder.add_node("search_recipes", recipe_search_graph)
```

### Parallel Execution with Send API

```python
from langgraph.types import Send

def fan_out_searches(state: MealPlanState):
    """Search multiple recipe sources in parallel."""
    sources = state["recipe_sources"]

    return [
        Send("search_source", {"source": source, "ingredients": state["ingredients"]})
        for source in sources
    ]

builder.add_conditional_edges(
    "prepare_search",
    fan_out_searches,
    ["search_source"]
)
```

---

## OpenAI/ChatGPT Integration

### Setup

```python
from langchain_openai import ChatOpenAI
import os

# Initialize ChatGPT
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
    streaming=True  # Enable for token streaming
)
```

### Tool Calling

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class RecipeSearchInput(BaseModel):
    query: str = Field(description="Search query for recipes")
    max_results: int = Field(default=10, description="Maximum results")

@tool(args_schema=RecipeSearchInput)
def search_recipes(query: str, max_results: int = 10) -> list:
    """Search for recipes on configured platforms."""
    # Implementation
    pass

# Bind tools to LLM
llm_with_tools = llm.bind_tools([search_recipes])
```

### Structured Output

```python
from langchain_core.output_parsers import PydanticOutputParser

class MealPlan(BaseModel):
    days: List[DayPlan]
    shopping_list: List[ShoppingItem]
    estimated_cost: float

parser = PydanticOutputParser(pydantic_object=MealPlan)

# Use in prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "Generate a meal plan. {format_instructions}"),
    ("user", "{input}")
]).partial(format_instructions=parser.get_format_instructions())
```

### Using LangGraph Prebuilt Agent

```python
from langgraph.prebuilt import create_react_agent

# Quick agent creation
agent = create_react_agent(
    llm,
    tools=[search_recipes, calculate_coverage, generate_shopping_list],
    state_modifier="You are a helpful meal planning assistant..."
)

result = agent.invoke({"messages": [("user", "Plan meals for the week")]})
```

---

## Production Deployment

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize on startup
    app.state.checkpointer = await AsyncPostgresSaver.from_conn_string(
        os.getenv("DATABASE_URL")
    )
    app.state.graph = build_meal_plan_graph().compile(
        checkpointer=app.state.checkpointer
    )
    yield
    # Cleanup on shutdown
    await app.state.checkpointer.close()

app = FastAPI(lifespan=lifespan)

@app.post("/api/meal-plan")
async def create_meal_plan(request: MealPlanRequest):
    config = {"configurable": {"thread_id": request.user_id}}
    result = await app.state.graph.ainvoke(request.to_state(), config)
    return result

@app.post("/api/meal-plan/feedback")
async def submit_feedback(request: FeedbackRequest):
    config = {"configurable": {"thread_id": request.user_id}}
    result = await app.state.graph.ainvoke(
        Command(resume=request.feedback),
        config
    )
    return result
```

### Deployment Configuration

```python
# Gunicorn with Uvicorn workers
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4  # Number of CPU cores
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

### Environment Variables

```env
# .env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@host:5432/kondateagent
SECRET_KEY=your-secret-key
YOUTUBE_API_KEY=...

# Optional: LangSmith for observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
```

### Rate Limiting and Caching

```python
from functools import lru_cache
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/meal-plan")
@limiter.limit("10/minute")
async def create_meal_plan(request: Request, data: MealPlanRequest):
    # Implementation
    pass

# Cache recipe searches
@lru_cache(maxsize=1000)
def cached_recipe_search(query: str, source: str) -> list:
    return search_recipes(query, source)
```

---

## Application to KondateAgent

### Mapping Requirements to LangGraph Features

| KondateAgent Requirement | LangGraph Solution |
|--------------------------|-------------------|
| Ingredient Collection Node | StateGraph node with ChatGPT NLU |
| Recipe Search Node | Multi-source node with parallel Send API |
| Meal Plan Generation Node | LLM node with structured output |
| Feedback Processing Node | Human-in-the-loop with interrupt |
| Shopping List Node | Calculation node with reducer state |
| Session Persistence | PostgresSaver checkpointer |
| Real-time Updates | Streaming with `stream_mode="messages"` |
| Iterative Refinement | Cyclic graph with conditional edges |

### State Schema for KondateAgent

```python
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import operator

class Ingredient(TypedDict):
    name: str
    quantity: Optional[str]
    unit: Optional[str]

class Recipe(TypedDict):
    id: str
    title: str
    url: str
    thumbnail: Optional[str]
    source: str  # "youtube" | "instagram"
    ingredients: List[Ingredient]
    coverage_score: float

class DayMeal(TypedDict):
    day: str
    breakfast: Optional[Recipe]
    lunch: Optional[Recipe]
    dinner: Optional[Recipe]

class ShoppingItem(TypedDict):
    ingredient: str
    quantity: str
    category: str  # "produce" | "protein" | "dairy" | "pantry"

class KondateState(TypedDict):
    """Complete state for the KondateAgent workflow."""
    # User session
    user_id: str

    # Conversation
    messages: Annotated[List[AnyMessage], add_messages]

    # Inputs
    raw_ingredients_input: str
    ingredients: List[Ingredient]
    dietary_restrictions: List[str]
    recipe_sources: List[dict]  # [{"type": "youtube", "channel_id": "..."}]

    # Recipe candidates
    recipe_candidates: List[Recipe]

    # Meal plan
    current_meal_plan: List[DayMeal]

    # Feedback loop
    user_feedback: Optional[str]
    feedback_history: Annotated[List[str], operator.add]
    iteration_count: int

    # Output
    shopping_list: List[ShoppingItem]
    plan_finalized: bool
```

---

## Recommended Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Ingredient│  │Meal Plan │  │ Feedback │  │ Shopping │        │
│  │  Input   │  │ Display  │  │Interface │  │   List   │        │
│  └────┬─────┘  └────▲─────┘  └────┬─────┘  └────▲─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │ WebSocket/SSE│             │             │
        ▼             │             ▼             │
┌───────┴─────────────┴─────────────┴─────────────┴───────────────┐
│                     FastAPI Backend                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   LangGraph Workflow                     │    │
│  │                                                          │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐          │    │
│  │  │Ingredient│───▶│  Recipe  │───▶│Meal Plan │          │    │
│  │  │  Parser  │    │  Search  │    │Generator │          │    │
│  │  └──────────┘    └──────────┘    └────┬─────┘          │    │
│  │                        ▲              │                  │    │
│  │                        │              ▼                  │    │
│  │                  ┌─────┴────┐   ┌──────────┐            │    │
│  │                  │ Feedback │◀──│  Wait    │            │    │
│  │                  │ Process  │   │ Feedback │            │    │
│  │                  └─────┬────┘   └──────────┘            │    │
│  │                        │                                 │    │
│  │                        ▼                                 │    │
│  │                  ┌──────────┐                           │    │
│  │                  │ Shopping │                           │    │
│  │                  │   List   │                           │    │
│  │                  └──────────┘                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                   ┌──────────▼──────────┐                       │
│                   │  PostgresSaver      │                       │
│                   │  (Checkpointer)     │                       │
│                   └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────┐
│   OpenAI API  │    │   YouTube API   │    │Instagram API │
│   (ChatGPT)   │    │                 │    │              │
└───────────────┘    └─────────────────┘    └──────────────┘
```

### Workflow Flow

```
START
  │
  ▼
┌─────────────────┐
│ Parse           │◀─── User: "I have chicken, tomatoes, rice..."
│ Ingredients     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Search          │───▶ YouTube API, Instagram API (parallel)
│ Recipes         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │───▶ ChatGPT: Optimize for ingredient usage
│ Meal Plan       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Wait for        │◀─── Interrupt (HITL)
│ Feedback        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Process         │
│ Feedback        │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
"regenerate" "finalize"
    │         │
    │         ▼
    │   ┌─────────────────┐
    │   │ Generate        │
    │   │ Shopping List   │
    │   └────────┬────────┘
    │            │
    │            ▼
    │          END
    │
    └──────▶ (back to Generate Meal Plan - max 3 iterations)
```

---

## Implementation Roadmap

### Phase 1: Core Workflow (Foundation)

1. **Set up project structure**
   - Create LangGraph workflow module
   - Define state schema with TypedDict
   - Set up FastAPI endpoints

2. **Implement basic nodes**
   - Ingredient parser (ChatGPT NLU)
   - Basic recipe search (mock data initially)
   - Meal plan generator

3. **Add persistence**
   - Integrate SqliteSaver for development
   - Add session management with thread_id

### Phase 2: External Integrations

1. **Recipe sources**
   - YouTube Data API integration
   - Instagram Graph API integration
   - Implement coverage score calculation

2. **Streaming**
   - Add token streaming for meal plan generation
   - Implement SSE endpoints for frontend

### Phase 3: Feedback Loop

1. **Human-in-the-loop**
   - Implement interrupt for feedback collection
   - Add conditional edges for regeneration
   - Implement iteration limits

2. **Shopping list optimization**
   - Calculate missing ingredients
   - Group by category
   - Prioritize shared ingredients

### Phase 4: Production Readiness

1. **Database**
   - Migrate to PostgresSaver
   - Add user authentication
   - Store user preferences

2. **Deployment**
   - Containerize with Docker
   - Set up Gunicorn + Uvicorn
   - Configure environment variables

3. **Monitoring**
   - Integrate LangSmith for observability
   - Add error handling and retries
   - Implement rate limiting

---

## References

### Official Documentation
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph GitHub Repository](https://github.com/langchain-ai/langgraph)
- [LangChain Academy - Intro to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
- [LangGraph PyPI Package](https://pypi.org/project/langgraph/)

### State Management
- [Mastering LangGraph State Management in 2025](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025)
- [LangGraph for Beginners: StateGraph](https://medium.com/ai-agents/langgraph-for-beginners-part-4-stategraph-794004555369)
- [LangGraph State with Pydantic BaseModel](https://medium.com/fundamentals-of-artificial-intelligence/langgraph-state-with-pydantic-basemodel-023a2158ab00)

### Persistence and Checkpointing
- [LangGraph Persistence Documentation](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph v0.2: Checkpointer Libraries](https://blog.langchain.com/langgraph-v0-2/)
- [langgraph-checkpoint-sqlite](https://pypi.org/project/langgraph-checkpoint-sqlite/)
- [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint/)

### Human-in-the-Loop
- [Making it Easier to Build HITL Agents with Interrupt](https://blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/)
- [Human-in-the-Loop with LangGraph: A Beginner's Guide](https://sangeethasaravanan.medium.com/human-in-the-loop-with-langgraph-a-beginners-guide-8a32b7f45d6e)
- [IBM: Human in the Loop Tutorial](https://www.ibm.com/think/tutorials/human-in-the-loop-ai-agent-langraph-watsonx-ai)

### Multi-Agent Systems
- [LangGraph Multi-Agent Workflows](https://www.blog.langchain.com/langgraph-multi-agent-workflows/)
- [LangGraph Supervisor Library](https://changelog.langchain.com/announcements/langgraph-supervisor-a-library-for-hierarchical-multi-agent-systems)
- [AWS: Build Multi-Agent Systems with LangGraph](https://aws.amazon.com/blogs/machine-learning/build-multi-agent-systems-with-langgraph-and-amazon-bedrock/)

### Streaming
- [LangGraph Streaming Documentation](https://docs.langchain.com/oss/python/langgraph/streaming)
- [LangGraph Streaming 101: 5 Modes](https://dev.to/sreeni5018/langgraph-streaming-101-5-modes-to-build-responsive-ai-applications-4p3f)
- [Building Real-Time AI Apps with LangGraph, FastAPI & Streamlit](https://medium.com/@dharamai2024/building-real-time-ai-apps-with-langgraph-fastapi-streamlit-streaming-llm-responses-like-04d252d4d763)

### Production Deployment
- [Build AI Workflows with FastAPI & LangGraph | 2025 Guide](https://www.zestminds.com/blog/build-ai-workflows-fastapi-langgraph/)
- [fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template)
- [Building Production-Ready AI APIs with FastAPI and LangGraph](https://medium.com/@yogeshkrishnanseeniraj/building-production-ready-ai-apis-with-fastapi-and-langgraph-165ca7d163b1)
- [FastAPI Production Deployment Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)

### OpenAI Integration
- [ChatOpenAI Documentation](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [Tool Calling with LangChain](https://blog.langchain.com/tool-calling-with-langchain/)
- [Building Tool Calling Agents with LangGraph](https://sangeethasaravanan.medium.com/building-tool-calling-agents-with-langgraph-a-complete-guide-ebdcdea8f475)

### Tutorials
- [DataCamp: LangGraph Tutorial](https://www.datacamp.com/tutorial/langgraph-tutorial)
- [Real Python: LangGraph Build Stateful AI Agents](https://realpython.com/langgraph-python/)
- [Codecademy: Building AI Workflow with LangGraph](https://www.codecademy.com/article/building-ai-workflow-with-langgraph)
- [Analytics Vidhya: LangGraph Tutorial for Beginners](https://www.analyticsvidhya.com/blog/2025/05/langgraph-tutorial-for-beginners/)

### Cyclic Workflows
- [IBM: What is LangGraph?](https://www.ibm.com/think/topics/langgraph)
- [Conditional Edge and Cycle in LangGraph Explained](https://blog.gopenai.com/conditional-edge-and-cycle-in-langgraph-explained-da4a112bf1ea)
- [From Basics to Advanced: Exploring LangGraph](https://towardsdatascience.com/from-basics-to-advanced-exploring-langgraph-e8c1cf4db787/)

---

## Conclusion

LangGraph provides an ideal framework for implementing the KondateAgent meal planning workflow. Its support for:

- **Cyclic graphs** enables the iterative feedback loops required for meal plan refinement
- **State management** with TypedDict/Pydantic maintains complex workflow state
- **Persistence** ensures sessions can be resumed and user history preserved
- **Human-in-the-loop** patterns align perfectly with user feedback requirements
- **Streaming** enables real-time UI updates for better user experience
- **Production patterns** with FastAPI provide a clear path to deployment

The recommended approach is to start with a simple linear workflow, then incrementally add the feedback cycle, external API integrations, and finally production-grade persistence and deployment.
