from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ingredients_router

app = FastAPI(title="KondateAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingredients_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
