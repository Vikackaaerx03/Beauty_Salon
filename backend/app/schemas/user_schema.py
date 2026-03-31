from __future__ import annotations
from datetime import datetime
from typing import Literal
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
UserRole = Literal['guest', 'client', 'admin', 'master']

def _ensure_valid_email(value: str | None) -> str | None:
    if value is None: return None
    normalized = value.strip()
    if not EMAIL_PATTERN.match(normalized):
        raise ValueError('email має бути user@domain.tld')
    return normalized

class UserBase(BaseModel):
    name: str
    email: str
    role: UserRole = 'client'
    rating: float = 0.0
    services_offered: list[str] = Field(default_factory=list)
    
    model_config = ConfigDict(populate_by_name=True)

    @field_validator('email')
    def validate_email(cls, value: str) -> str:
        cleaned = _ensure_valid_email(value)
        assert cleaned is not None
        return cleaned

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    role: UserRole | None = None
    rating: float | None = None
    services_offered: list[str] | None = None

    @field_validator('email', mode='before')
    def validate_update_email(cls, value: str | None) -> str | None:
        return _ensure_valid_email(value)

class UserDB(UserBase):
    id: str
    created_at: datetime