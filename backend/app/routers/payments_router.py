from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_payments_collection
from app.repositories.payments_repository import PaymentRepository
from app.services.payments_service import PaymentsService
from app.schemas.payments_schema import PaymentCreate, PaymentDB, PaymentUpdate

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payments_service(collection=Depends(get_payments_collection)) -> PaymentsService:
    return PaymentsService(PaymentRepository(collection))


@router.post("", response_model=PaymentDB, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, service: PaymentsService = Depends(get_payments_service)):
    return service.create(payload)


@router.get("", response_model=list[PaymentDB])
def list_payments(booking_id: str | None = None, service: PaymentsService = Depends(get_payments_service)):
    return service.list(booking_id=booking_id)


@router.get("/{payment_id}", response_model=PaymentDB)
def get_payment(payment_id: str, service: PaymentsService = Depends(get_payments_service)):
    try:
        return service.get(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{payment_id}", response_model=PaymentDB)
def update_payment(payment_id: str, payload: PaymentUpdate, service: PaymentsService = Depends(get_payments_service)):
    try:
        return service.update(payment_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: str, service: PaymentsService = Depends(get_payments_service)):
    try:
        service.delete(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
