from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories import UserRepository
from app.schemas.auth import TokenData


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)

    async def register(self, email: str, password: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise AppException(
                code=40901,
                message="email_already_exists",
                status_code=409,
            )
        password_hash = hash_password(password)
        return await self.users.create(email=email, password_hash=password_hash)

    async def login(self, email: str, password: str) -> TokenData:
        if not settings.jwt_secret:
            raise AppException(
                code=50301,
                message="auth_not_configured",
                status_code=503,
            )
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AppException(
                code=40102,
                message="invalid_credentials",
                status_code=401,
            )
        token = create_access_token(str(user.id))
        return TokenData(access_token=token)
