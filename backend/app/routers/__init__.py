from .auth import router as auth_router
from .ingredients import router as ingredients_router
from .recipes import router as recipes_router
from .creators import router as creators_router

__all__ = ["auth_router", "ingredients_router", "recipes_router", "creators_router"]
