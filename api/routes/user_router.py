from fastapi import APIRouter, HTTPException

from api.dependencies import CurrentUser, UserServiceDep
from api.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


# --- Autenticación ---


@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user_in: UserCreate, service: UserServiceDep):
    try:
        return service.register(user_in)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, service: UserServiceDep):
    try:
        return service.login(credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    return current_user


# --- Gestión de usuarios ---


@router.get("/users", response_model=list[UserResponse])
def get_users(service: UserServiceDep, _: CurrentUser):
    return service.get_users()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, service: UserServiceDep, _: CurrentUser):
    try:
        return service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    service: UserServiceDep,
    _: CurrentUser,
):
    try:
        return service.update_user(user_id, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, service: UserServiceDep, _: CurrentUser):
    try:
        service.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
