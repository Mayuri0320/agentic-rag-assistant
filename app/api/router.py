"""Main API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, documents, health, me, root

api_router = APIRouter()

api_router.include_router(root.router)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
