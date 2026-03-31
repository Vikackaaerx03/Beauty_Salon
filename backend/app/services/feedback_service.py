from __future__ import annotations
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback_schema import FeedbackCreate

class FeedbackService:
    def __init__(self, repo: FeedbackRepository):
        self.repo = repo

    def create(self, payload: FeedbackCreate) -> dict:
        feedback_id = self.repo.create(payload)
        feedback = self.repo.get_by_id(feedback_id)
        if feedback is None:
            raise RuntimeError("Помилка при створенні відгуку")
        return feedback

    def get(self, feedback_id: str) -> dict:
        feedback = self.repo.get_by_id(feedback_id)
        if feedback is None:
            raise ValueError("Відгук не знайдено")
        return feedback

    def list(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        return self.repo.get_all(client_id=client_id, master_id=master_id)

    def update(self, feedback_id: str, payload: FeedbackCreate) -> dict:
        update_data = payload.model_dump()
        updated_feedback = self.repo.update(feedback_id, update_data)
        if updated_feedback is None:
            raise ValueError("Відгук не знайдено для оновлення")
        return updated_feedback

    def delete(self, feedback_id: str) -> None:
        deleted = self.repo.delete(feedback_id)
        if deleted == 0:
            raise ValueError("Відгук не знайдено")