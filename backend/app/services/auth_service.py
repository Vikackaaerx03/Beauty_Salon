from __future__ import annotations
from datetime import datetime
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

    def login(self, payload: AuthLogin) -> dict:
        # 1. Шукаємо користувача
        user = self.repo.find_by_email(payload.email)
        if not user:
            raise ValueError("Невірний email або пароль")

        if not verify_password(payload.password, user["password_hash"]):
            raise ValueError("Невірний email або пароль")

        user_id = str(user.get("id") or user.get("_id"))
        
        token_data = {"sub": user_id, "email": user["email"], "role": user["role"]}
        access_token = create_access_token(token_data)

        return {
            "token": {
                "access_token": access_token,
                "token_type": "bearer"
            },
            "user": {
                "id": user_id,
                "name": user.get("name"),
                "email": user["email"],
                "role": user["role"],
                "rating": user.get("rating", 0.0),
                "services_offered": [str(s) for s in (user.get("services_offered") or [])],
                "created_at": user.get("created_at") or datetime.utcnow()
            }
        }

    def _issue_token(self, user_id: str, role: str) -> str:
        settings = get_settings()
        return create_access_token(
            {"sub": user_id, "role": role}
        )