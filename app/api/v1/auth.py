from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(db, user_in)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive access + refresh tokens",
)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login_user(db, login_in)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair (rotation)",
)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db, body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh token",
)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.logout_user(db, body.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
