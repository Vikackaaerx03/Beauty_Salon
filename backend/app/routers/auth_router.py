from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_users_collection
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth_schema import AuthLogin, AuthRegister, AuthResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(collection=Depends(get_users_collection)) -> AuthService:
    return AuthService(AuthRepository(collection))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegister, service: AuthService = Depends(get_auth_service)):
    try:
        return service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLogin, service: AuthService = Depends(get_auth_service)):
    try:
        return service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
