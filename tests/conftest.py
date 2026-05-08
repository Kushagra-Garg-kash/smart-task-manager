"""
Test configuration using an in-memory SQLite database.
No real PostgreSQL needed for unit/integration tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session

from app.db.base_class import Base
from app.db.session import get_db
import app.main as main_module

# Import all models so Base.metadata knows about them
import app.db.base  # noqa: F401

SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=False)
def db() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    main_module.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main_module.app) as c:
        yield c
    main_module.app.dependency_overrides.clear()


# ─── Helper factories ──────────────────────────────────────────────────────────

def create_test_user(
    client: TestClient,
    email: str = "test@example.com",
    password: str = "testpass123",
    full_name: str = "Test User",
) -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def login_test_user(
    client: TestClient,
    email: str = "test@example.com",
    password: str = "testpass123",
) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth_headers(client: TestClient, email: str = "test@example.com", password: str = "testpass123") -> dict:
    tokens = login_test_user(client, email, password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
