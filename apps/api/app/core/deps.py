import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.models import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    """JWT-only — safe for long-lived SSE (does not hold a DB session)."""
    if not settings.jwt_secret:
        raise AppException(
            code=50301,
            message="auth_not_configured",
            status_code=503,
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppException(
            code=40101,
            message="not_authenticated",
            status_code=401,
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise AppException(
            code=40101,
            message="invalid_token",
            status_code=401,
        ) from None
    sub = payload.get("sub")
    if not sub:
        raise AppException(code=40101, message="invalid_token", status_code=401)
    try:
        return uuid.UUID(str(sub))
    except ValueError:
        raise AppException(code=40101, message="invalid_token", status_code=401)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not settings.jwt_secret:
        raise AppException(
            code=50301,
            message="auth_not_configured",
            status_code=503,
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppException(
            code=40101,
            message="not_authenticated",
            status_code=401,
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise AppException(
            code=40101,
            message="invalid_token",
            status_code=401,
        ) from None
    sub = payload.get("sub")
    if not sub:
        raise AppException(code=40101, message="invalid_token", status_code=401)
    try:
        user_id = uuid.UUID(str(sub))
    except ValueError:
        raise AppException(code=40101, message="invalid_token", status_code=401)
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        # Token 有效但用户已删除：仍返回 401，避免泄露用户是否存在
        raise AppException(code=40101, message="invalid_token", status_code=401)
    return user
