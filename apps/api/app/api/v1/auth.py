from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success
from app.schemas.auth import AuthLogin, AuthRegister
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: AuthRegister,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(email=body.email, password=body.password)
    await db.commit()
    return success(data=UserRead.model_validate(user).model_dump())


@router.post("/login")
async def login(
    body: AuthLogin,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token = await service.login(email=body.email, password=body.password)
    return success(data=token.model_dump())
