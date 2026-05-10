from __future__ import annotations

from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.user_repository import UserRepository
from app.schemas.feedback_schema import FeedbackCreate


class FeedbackService:
    def __init__(self, repo: FeedbackRepository, users: UserRepository | None = None):
        self.repo = repo
        self.users = users

    def _enrich_feedback(self, feedback: dict | None) -> dict | None:
        if feedback is None:
            return None

        enriched = dict(feedback)
        if self.users:
            client = self.users.get_by_id(enriched.get("client_id"))
            master = self.users.get_by_id(enriched.get("master_id"))
            if client:
                enriched["client_name"] = client.get("name")
            if master:
                enriched["master_name"] = master.get("name")
        return enriched

    def create(self, payload: FeedbackCreate) -> dict:
        feedback_id = self.repo.create(payload)
        feedback = self.repo.get_by_id(feedback_id)
        if feedback is None:
            raise RuntimeError("Помилка при створенні відгуку")
        return self._enrich_feedback(feedback)

    def get(self, feedback_id: str) -> dict:
        feedback = self.repo.get_by_id(feedback_id)
        if feedback is None:
            raise ValueError("Відгук не знайдено")
        return self._enrich_feedback(feedback)

    def list(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        return [
            feedback
            for feedback in (self._enrich_feedback(item) for item in self.repo.get_all(client_id=client_id, master_id=master_id))
            if feedback is not None
        ]

    def update(self, feedback_id: str, payload: FeedbackCreate) -> dict:
        update_data = payload.model_dump()
        updated_feedback = self.repo.update(feedback_id, update_data)
        if updated_feedback is None:
            raise ValueError("Відгук не знайдено для оновлення")
        return self._enrich_feedback(updated_feedback)

    def delete(self, feedback_id: str) -> None:
        deleted = self.repo.delete(feedback_id)
        if deleted == 0:
            raise ValueError("Відгук не знайдено")
