"""Test fixtures: isolated file-backed SQLite DB, seeded categories, clean tables per test."""

import os
import tempfile

# Must be set before the app modules are imported.
_tmpdir = tempfile.mkdtemp(prefix="shamba-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-tests-1234567890"
os.environ["ENVIRONMENT"] = "test"
os.environ["FRONTEND_ORIGIN"] = "http://testserver"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal, engine
from app.main import app
from app.models.domain import Base, FarmRecord, User
from app.rate_limit import clear_rate_limits

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_state():
    clear_rate_limits()
    with SessionLocal() as db:
        db.execute(delete(FarmRecord))
        db.execute(delete(User))
        db.commit()
    yield
    clear_rate_limits()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, email: str = "farmer@example.com", password: str = "password123") -> dict:
    response = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
