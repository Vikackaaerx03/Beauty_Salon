from __future__ import annotations

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth_schema import AuthLogin, AuthRegister, AuthResponse, TokenResponse


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def register(self, payload: AuthRegister) -> AuthResponse:
        existing = self.repo.find_by_email(payload.email)
        if existing is not None:
            raise ValueError("Email already exists")

        user_id = self.repo.register(payload)
        user = self.repo.get_public_by_id(user_id)
        if user is None:
            raise RuntimeError("Failed to create user")

        token = self._issue_token(user_id=user_id, role=str(user.get("role", "client")))
        return AuthResponse(token=TokenResponse(access_token=token), user=user)

    def login(self, payload: AuthLogin) -> AuthResponse:
        doc = self.repo.find_by_email(payload.email)
        if doc is None:
            raise ValueError("Invalid credentials")

        password_hash = doc.get("password_hash")
        if not isinstance(password_hash, str) or not verify_password(payload.password, password_hash):
            raise ValueError("Invalid credentials")

        user_id = str(doc["_id"])
        user = self.repo.get_public_by_id(user_id)
        if user is None:
            raise RuntimeError("Failed to load user")

        token = self._issue_token(user_id=user_id, role=str(user.get("role", "client")))
        return AuthResponse(token=TokenResponse(access_token=token), user=user)

    def _issue_token(self, user_id: str, role: str) -> str:
        settings = get_settings()
        return create_access_token(
            {"sub": user_id, "role": role, "exp_min": settings.ACCESS_TOKEN_EXPIRE_MINUTES}
        )
