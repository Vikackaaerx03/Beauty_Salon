from pydantic import BaseModel, EmailStr

from app.schemas.user_schema import UserDB


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class AuthRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "client"  # guest, client, admin, master


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserDB
