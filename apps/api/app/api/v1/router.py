from fastapi import APIRouter

from app.api.v1 import auth, chat, conversations, health, knowledge, me, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(users.router)
api_router.include_router(conversations.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
