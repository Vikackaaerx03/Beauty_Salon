from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.user_schema import UserDB, _ensure_valid_email

RegisterRole = Literal["client", "master"]


class AuthLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, value: str) -> str:
        cleaned = _ensure_valid_email(value)
        assert cleaned is not None
        return cleaned


class AuthRegister(BaseModel):
    name: str
    email: str
    password: str
    role: RegisterRole = "client"

    @field_validator("email")
    def validate_email(cls, value: str) -> str:
        cleaned = _ensure_valid_email(value)
        assert cleaned is not None
        return cleaned


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserDB
