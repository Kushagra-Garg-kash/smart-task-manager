import pytest
import time
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_access_token, decode_refresh_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "supersecret"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_two_hashes_differ(self):
        """bcrypt uses a random salt, so same password → different hash."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestJWTTokens:
    def test_access_token_round_trip(self):
        token = create_access_token(subject=42)
        user_id = decode_access_token(token)
        assert user_id == "42"

    def test_refresh_token_round_trip(self):
        token = create_refresh_token(subject=99)
        user_id = decode_refresh_token(token)
        assert user_id == "99"

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token(subject=1)
        assert decode_refresh_token(token) is None

    def test_refresh_token_rejected_as_access(self):
        token = create_refresh_token(subject=1)
        assert decode_access_token(token) is None

    def test_tampered_token_rejected(self):
        token = create_access_token(subject=1)
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.token") is None
        assert decode_refresh_token("not.a.token") is None
