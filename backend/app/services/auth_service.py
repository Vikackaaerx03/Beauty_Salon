from __future__ import annotations

from datetime import datetime

from app.core.security import create_access_token, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth_schema import AuthLogin, AuthRegister, AuthResponse, TokenResponse


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def register(self, payload: AuthRegister) -> AuthResponse:
        if payload.role not in {"client", "master"}:
            raise ValueError("Registration role must be client or master")

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
        user = self.repo.find_by_email(payload.email)
        if not user:
            raise ValueError("Невірний email або пароль")

        if not verify_password(payload.password, user["password_hash"]):
            raise ValueError("Невірний email або пароль")

        user_id = str(user.get("id") or user.get("_id"))
        access_token = self._issue_token(user_id=user_id, role=str(user.get("role", "client")))
        public_user = self.repo.get_public_by_id(user_id)

        if public_user is None:
            raise RuntimeError("Failed to load user profile")

        public_user.setdefault("created_at", user.get("created_at") or datetime.utcnow())
        return AuthResponse(token=TokenResponse(access_token=access_token), user=public_user)

    def _issue_token(self, user_id: str, role: str) -> str:
        return create_access_token({"sub": user_id, "role": role})
