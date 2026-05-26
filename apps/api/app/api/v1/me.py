from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.response import success
from app.models import User
from app.schemas.user import UserRead

router = APIRouter(tags=["auth"])


@router.get("/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return success(data=UserRead.model_validate(current_user).model_dump())
