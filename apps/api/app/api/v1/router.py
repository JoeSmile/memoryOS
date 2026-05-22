from fastapi import APIRouter

from app.api.v1 import conversations, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(conversations.router)
