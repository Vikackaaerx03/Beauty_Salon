from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_admin, get_current_user, logger
from app.db.database import get_bookings_collection, get_feedback_collection, get_payments_collection
from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.schemas.feedback_schema import FeedbackCreate, FeedbackDB
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def get_feedback_service(collection=Depends(get_feedback_collection)) -> FeedbackService:
    return FeedbackService(FeedbackRepository(collection))


@router.post("", response_model=FeedbackDB, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
    current_user: dict = Depends(get_current_user),
    bookings_collection=Depends(get_bookings_collection),
    payments_collection=Depends(get_payments_collection),
):
    if current_user.get("role") != "admin":
        if current_user.get("id") != str(payload.client_id):
            raise HTTPException(status_code=403, detail="Відгук може залишити лише власник запису")

        booking = BookingRepository(bookings_collection).get_by_id(payload.booking_id)
        if booking is None:
            raise HTTPException(status_code=404, detail="Запис не знайдено")
        if booking.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Відгук доступний лише після завершеної послуги")

        payments = PaymentRepository(payments_collection).get_all(booking_id=str(payload.booking_id))
        if not any(payment.get("status") == "paid" for payment in payments):
            raise HTTPException(status_code=400, detail="Відгук доступний лише після оплати")

    try:
        created = service.create(payload)
        logger.info("%s %s створив відгук для бронювання %s", current_user.get("role"), current_user.get("email"), payload.booking_id)
        return created
    except ValueError as exc:
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
    current_admin: dict = Depends(get_current_admin),
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
