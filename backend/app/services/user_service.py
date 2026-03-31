from __future__ import annotations
from typing import List, Optional
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_all(self, role: str | None = None, service_id: str | None = None, sort_by: str | None = None) -> List[dict]:
        return self.repo.get_all(role=role, service_id=service_id, sort_by=sort_by)

    def get_by_id(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Користувача не знайдено")
        return user

    def create(self, payload: UserCreate) -> dict:
        user_id = self.repo.create(payload)
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise RuntimeError("Не вдалося створити користувача")
        return user

    def update(self, user_id: str, payload: UserUpdate) -> dict:
        self.repo.update(user_id, payload)
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Користувача не знайдено")
        return user

    def delete(self, user_id: str) -> None:
        if self.repo.delete(user_id) == 0:
            raise ValueError("Користувача не знайдено")