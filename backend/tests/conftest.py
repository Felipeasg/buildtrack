"""Test fixtures.

Tests run against an isolated in-memory SQLite database (via a dependency
override) so they never touch the real Postgres data and start from a clean
schema every run. The models only use portable column types, so SQLite is a
faithful stand-in for the auth/CRUD behaviour under test.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user_credentials():
    return {
        "email": "builder@example.com",
        "password": "secret123",
        "full_name": "Sam Builder",
    }


@pytest.fixture
def auth_token(client, user_credentials):
    """Register a user and return a valid bearer token."""
    res = client.post("/api/auth/register", json=user_credentials)
    assert res.status_code == 201, res.text
    return res.json()["access_token"]
