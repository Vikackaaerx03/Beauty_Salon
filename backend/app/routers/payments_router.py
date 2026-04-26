from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_admin, get_current_user, logger
from app.db.database import get_bookings_collection, get_payments_collection
from app.repositories.booking_repository import BookingRepository
from app.repositories.payments_repository import PaymentRepository
from app.schemas.payments_schema import PaymentCreate, PaymentDB, PaymentUpdate
from app.services.payments_service import PaymentsService

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payments_service(collection=Depends(get_payments_collection)) -> PaymentsService:
    return PaymentsService(PaymentRepository(collection))


@router.post("", response_model=PaymentDB, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    service: PaymentsService = Depends(get_payments_service),
    current_admin: dict = Depends(get_current_admin),
):
    created = service.create(payload)
    logger.info("Адмін %s створив платіж для бронювання %s", current_admin.get("email"), payload.booking_id)
    return created


@router.get("", response_model=list[PaymentDB])
def list_payments(
    booking_id: str | None = None,
    service: PaymentsService = Depends(get_payments_service),
    current_admin: dict = Depends(get_current_admin),
):
    return service.list(booking_id=booking_id)


@router.get("/{payment_id}", response_model=PaymentDB)
def get_payment(
    payment_id: str,
    service: PaymentsService = Depends(get_payments_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        return service.get(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/booking/{booking_id}", response_model=list[PaymentDB])
def list_payments_for_booking(
    booking_id: str,
    service: PaymentsService = Depends(get_payments_service),
    current_user: dict = Depends(get_current_user),
    bookings_collection=Depends(get_bookings_collection),
):
    booking = BookingRepository(bookings_collection).get_by_id(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.get("role") != "admin" and current_user.get("id") not in {str(booking.get("client_id")), str(booking.get("master_id"))}:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    return service.list(booking_id=booking_id)


@router.patch("/{payment_id}", response_model=PaymentDB)
def update_payment(
    payment_id: str,
    payload: PaymentUpdate,
    service: PaymentsService = Depends(get_payments_service),
    current_user: dict = Depends(get_current_user),
    bookings_collection=Depends(get_bookings_collection),
):
    payment = service.get(payment_id)
    booking = BookingRepository(bookings_collection).get_by_id(payment.get("booking_id"))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.get("role") != "admin" and current_user.get("id") != str(booking.get("master_id")):
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    try:
        updated = service.update(payment_id, payload)
        logger.info("%s %s оновив платіж %s", current_user.get("role"), current_user.get("email"), payment_id)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{payment_id}/accept", response_model=PaymentDB)
def accept_payment(
    payment_id: str,
    service: PaymentsService = Depends(get_payments_service),
    current_user: dict = Depends(get_current_user),
    bookings_collection=Depends(get_bookings_collection),
):
    payment = service.get(payment_id)
    booking = BookingRepository(bookings_collection).get_by_id(payment.get("booking_id"))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.get("role") != "admin" and current_user.get("id") != str(booking.get("master_id")):
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    try:
        updated = service.update(payment_id, PaymentUpdate(status="paid"))
        logger.info("%s %s прийняв оплату %s", current_user.get("role"), current_user.get("email"), payment_id)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: str,
    service: PaymentsService = Depends(get_payments_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(payment_id)
        logger.info("Адмін %s видалив платіж %s", current_admin.get("email"), payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
