"""Main API router."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.debug import router as debug_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.me import router as me_router
from app.api.v1.endpoints.root import router as root_router

api_router = APIRouter()

api_router.routes.extend(root_router.routes)
api_router.routes.extend(health_router.routes)
api_router.routes.extend(debug_router.routes)
api_router.routes.extend(auth_router.routes)
api_router.routes.extend(me_router.routes)
