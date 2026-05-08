import pytest
from fastapi.testclient import TestClient
from tests.conftest import create_test_user, login_test_user, auth_headers


class TestRegister:
    def test_register_success(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "password123", "full_name": "New User"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient):
        create_test_user(client)
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123", "full_name": "Dup"},
        )
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_weak_password(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "password": "short", "full_name": "Weak"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient):
        create_test_user(client)
        tokens = login_test_user(client)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        create_test_user(client)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert resp.status_code == 401


class TestTokenRefresh:
    def test_refresh_success(self, client: TestClient):
        create_test_user(client)
        tokens = login_test_user(client)
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # New refresh token should differ (rotation)
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

    def test_reuse_revoked_refresh_token(self, client: TestClient):
        """Old refresh token must be rejected after rotation."""
        create_test_user(client)
        tokens = login_test_user(client)
        # First use → rotates token
        client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        # Second use of the same old token → must fail
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 401

    def test_invalid_refresh_token(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "totally.invalid.token"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_get_me(self, client: TestClient):
        create_test_user(client)
        headers = auth_headers(client)
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_no_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        
