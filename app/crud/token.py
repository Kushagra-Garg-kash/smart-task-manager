from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.token import RefreshToken


def create_refresh_token(db: Session, token: str, user_id: int, expires_at: datetime) -> RefreshToken:
    rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def revoke_token(db: Session, rt: RefreshToken) -> None:
    rt.is_revoked = True
    db.commit()


def revoke_all_user_tokens(db: Session, user_id: int) -> None:
    """Revoke all active refresh tokens for a user (e.g. on password change)."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,
    ).update({"is_revoked": True})
    db.commit()


def cleanup_expired_tokens(db: Session) -> int:
    """Delete tokens past their expiry. Returns count deleted."""
    count = (
        db.query(RefreshToken)
        .filter(RefreshToken.expires_at < datetime.now(timezone.utc))
        .delete()
    )
    db.commit()
    return count
