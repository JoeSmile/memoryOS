from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """开发/测试用：创建用户（JWT 前临时接口）。"""
    service = UserService(db)
    user = await service.create(email=body.email)
    await db.commit()
    return success(data=UserRead.model_validate(user).model_dump())
