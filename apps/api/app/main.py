from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.response import success
from app.schemas.common import HealthData

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health", tags=["health"])
async def root_health():
    """根路径健康检查（Story 1.4）。"""
    return success(
        data=HealthData(
            status="ok",
            app=settings.app_name,
            env=settings.env,
        ).model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")
