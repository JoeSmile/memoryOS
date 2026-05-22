from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import User
from app.repositories import UserRepository


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)

    async def create(self, email: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise AppException(
                code=40901,
                message="email_already_exists",
                status_code=409,
            )
        return await self.users.create(email=email)
