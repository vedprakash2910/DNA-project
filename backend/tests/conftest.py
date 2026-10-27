import pytest
from fastapi.testclient import TestClient

import config as app_config
from dependencies import get_current_user
from main import app
from utils import security

FAKE_USER = {
    "id": "test-user",
    "email": "test@example.com",
    "role": "user",
    "created_at": "2026-01-01T00:00:00+00:00",
}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_auth: run with real JWT authentication (no dependency override)"
    )


@pytest.fixture(autouse=True)
def _isolated_db_and_cheap_hashing(tmp_path, monkeypatch):
    """Every test gets its own empty database, and password hashing is made cheap."""
    monkeypatch.setattr(app_config, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(security, "SCRYPT_N", 2 ** 10)


@pytest.fixture(autouse=True)
def _bypass_auth_for_legacy_tests(request):
    """The DNA endpoints now need a token. Older tests don't care about auth, so
    they run as a fake logged-in user. Tests marked `real_auth` use the real thing."""
    if request.node.get_closest_marker("real_auth"):
        yield
        return
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def client():
    # raise_server_exceptions=False -> unhandled errors come back as a real 500
    # response (what a browser would see) instead of re-raising inside the test.
    return TestClient(app, raise_server_exceptions=False)


def upload(client, reference=("ref.fasta", b">r\nATGC\n"), sample=("sample.fasta", b">s\nATGA\n")):
    return client.post(
        "/api/dna/upload",
        files={"reference_file": reference, "sample_file": sample},
    )


# ---- auth helpers (used by test_auth.py / test_records.py) -----------------
PASSWORD = "correct-horse-1"


def register(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def login(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def token_for(client, email="alice@example.com", password=PASSWORD):
    register(client, email, password)
    return login(client, email, password).json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
