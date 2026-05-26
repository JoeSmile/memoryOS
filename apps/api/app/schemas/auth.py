from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings


class AuthRegister(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
    )


class AuthLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=settings.password_max_length)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
