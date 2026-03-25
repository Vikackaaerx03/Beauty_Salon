from __future__ import annotations

from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create(self, payload: UserCreate) -> dict:
        user_id = self.repo.create(payload)
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise RuntimeError("Failed to create user")
        return user

    def get(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    def list(self, role: str | None = None, service_id: str | None = None, sort_by: str | None = None) -> list[dict]:
        return self.repo.get_all(role=role, service_id=service_id, sort_by=sort_by)

    def update(self, user_id: str, payload: UserUpdate) -> dict:
        updated = self.repo.update(user_id, payload)
        if updated == 0:
            existing = self.repo.get_by_id(user_id)
            if existing is None:
                raise ValueError("User not found")
            return existing
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    def delete(self, user_id: str) -> None:
        deleted = self.repo.delete(user_id)
        if deleted == 0:
            raise ValueError("User not found")
