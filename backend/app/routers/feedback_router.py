from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin, logger
from app.db.database import get_feedback_collection
from app.repositories.feedback_repository import FeedbackRepository
from app.services.feedback_service import FeedbackService
from app.schemas.feedback_schema import FeedbackCreate, FeedbackDB

router = APIRouter(prefix="/feedback", tags=["Feedback"])

def get_feedback_service(collection=Depends(get_feedback_collection)) -> FeedbackService:
    return FeedbackService(FeedbackRepository(collection))

@router.post("", response_model=FeedbackDB, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, service: FeedbackService = Depends(get_feedback_service)):
    try:
        return service.create(payload)
    except ValueError as exc:
        # Тепер фронтенд отримає текст помилки, а не Internal Server Error
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("", response_model=list[FeedbackDB])
def list_feedback(
    client_id: str | None = None,
    master_id: str | None = None,
    service: FeedbackService = Depends(get_feedback_service),
):
    return service.list(client_id=client_id, master_id=master_id)

@router.get("/{feedback_id}", response_model=FeedbackDB)
def get_feedback(feedback_id: str, service: FeedbackService = Depends(get_feedback_service)):
    try:
        return service.get(feedback_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    
@router.patch("/{feedback_id}", response_model=FeedbackDB)
def update_feedback(
    feedback_id: str, 
    payload: FeedbackCreate, 
    service: FeedbackService = Depends(get_feedback_service),
    current_admin: dict = Depends(get_current_admin) # Якщо редагувати може тільки адмін
):
    try:
        updated = service.update(feedback_id, payload)
        logger.info("Адмін %s оновив відгук %s", current_admin.get("email"), feedback_id)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: str,
    service: FeedbackService = Depends(get_feedback_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(feedback_id)
        logger.info("Адмін %s видалив відгук %s", current_admin.get("email"), feedback_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))