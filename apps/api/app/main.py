from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.redis import close_redis
from app.core.response import success
from app.middleware.injection_guard import InjectionGuardMiddleware
from app.services.health_service import build_health_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(InjectionGuardMiddleware)

register_exception_handlers(app)


@app.get("/health", tags=["health"])
async def root_health():
    """根路径健康检查（Story 1.4）。"""
    return success(data=await build_health_data())


app.include_router(api_router, prefix="/api/v1")
