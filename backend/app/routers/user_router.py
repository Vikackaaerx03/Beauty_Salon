from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin, logger
from app.db.database import get_users_collection
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserDB, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(collection=Depends(get_users_collection)) -> UserService:
    return UserService(UserRepository(collection))

@router.get("/masters", response_model=list[UserDB])
def get_masters(sort: str | None = None, service: UserService = Depends(get_user_service)):
    return service.get_all(role="master", sort_by=sort)

@router.post("", response_model=UserDB, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):
    try:
        created = service.create(payload)
        logger.info("Адмін %s створив користувача %s", current_admin.get("email"), payload.email)
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[UserDB])
def list_users(role: str | None = None, service_id: str | None = None, sort_by: str | None = None, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):

    return service.get_all(role=role, service_id=service_id, sort_by=sort_by)

@router.get("/{user_id}", response_model=UserDB)
def get_user(user_id: str, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):
    try:
        return service.get_by_id(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.patch("/{user_id}", response_model=UserDB)
def update_user(user_id: str, payload: UserUpdate, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):
    try:
        return service.update(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):
    try:
        service.delete(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))