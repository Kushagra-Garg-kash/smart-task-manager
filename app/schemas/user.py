from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole


# ─── Base ─────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: str


# ─── Create ───────────────────────────────────────────────────────────────────

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


# ─── Update ───────────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None


# ─── Response ─────────────────────────────────────────────────────────────────

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Minimal user info safe to embed in other responses."""
    id: int
    full_name: str
    email: EmailStr

    model_config = {"from_attributes": True}
