from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token as _create_refresh_jwt,
    decode_refresh_token,
)
from app.core.config import settings
from app.crud import user as user_crud
from app.crud import token as token_crud
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse


def register_user(db: Session, user_in: UserCreate) -> UserResponse:
    existing = user_crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = user_crud.create_user(db, user_in)
    return UserResponse.model_validate(user)


def login_user(db: Session, login_in: LoginRequest) -> TokenResponse:
    user = user_crud.get_user_by_email(db, login_in.email)
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(subject=user.id)
    refresh_jwt = _create_refresh_jwt(subject=user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    token_crud.create_refresh_token(db, refresh_jwt, user.id, expires_at)

    return TokenResponse(access_token=access_token, refresh_token=refresh_jwt)


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    # Decode JWT
    user_id_str = decode_refresh_token(refresh_token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check DB record (not revoked, not expired)
    rt = token_crud.get_refresh_token(db, refresh_token)
    if not rt or rt.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    if rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Token rotation: revoke old, issue new pair
    token_crud.revoke_token(db, rt)

    user = user_crud.get_user(db, int(user_id_str))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or deactivated",
        )

    access_token = create_access_token(subject=user.id)
    new_refresh_jwt = _create_refresh_jwt(subject=user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    token_crud.create_refresh_token(db, new_refresh_jwt, user.id, expires_at)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_jwt)


def logout_user(db: Session, refresh_token: str) -> None:
    rt = token_crud.get_refresh_token(db, refresh_token)
    if rt:
        token_crud.revoke_token(db, rt)
