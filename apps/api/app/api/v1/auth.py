import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.rate_limit import client_ip, enforce_login_rate_limit, enforce_register_rate_limit
from app.core.response import success
from app.repositories.audit_repository import AuditRepository
from app.schemas.auth import AuthLogin, AuthRegister
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: AuthRegister,
    _: None = Depends(enforce_register_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(email=body.email, password=body.password)
    await db.commit()
    return success(data=UserRead.model_validate(user).model_dump())


@router.post("/login")
async def login(
    body: AuthLogin,
    request: Request,
    _: None = Depends(enforce_login_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        token = await service.login(email=body.email, password=body.password)
    except AppException as exc:
        if exc.code == 40102:
            try:
                await AuditRepository(db).append_login_failed(
                    email=body.email,
                    ip_address=client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                )
                await db.commit()
            except Exception:
                logger.exception("audit_append_failed action=login_failed")
                await db.rollback()
        raise
    return success(data=token.model_dump())
