from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["guest", "client", "admin", "master"]


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = "client"
    rating: float = 0.0
    services_offered: list[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None
    rating: float | None = None
    services_offered: list[str] | None = None


class UserDB(UserBase):
    id: str
    created_at: datetime
