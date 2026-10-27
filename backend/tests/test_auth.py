"""HTTP tests for registration, login, JWT checks and protected routes.

Needs requirements.txt + requirements-dev.txt.  Run:  python -m pytest tests/test_auth.py -v
"""
import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest

import config
from tests.conftest import PASSWORD, auth, login, register, token_for
from utils import security
from utils.database import get_connection

pytestmark = pytest.mark.real_auth   # use real JWT auth, not the test bypass

PROTECTED_GET = "/api/auth/me"
BODY = {"reference": "ATGCATGC", "sample": "ATGTATGC"}


# ------------------------------------------------------------ registration
def test_register_ok_never_returns_password_or_hash(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["role"] == "user"
    assert "password" not in r.text and "hash" not in r.text


def test_register_cannot_choose_role(client):
    r = client.post("/api/auth/register",
                    json={"email": "evil@example.com", "password": PASSWORD, "role": "admin"})
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "user"


def test_register_duplicate_email_is_409(client):
    register(client)
    r = register(client, email="ALICE@example.com")
    assert r.status_code == 409
    assert r.json()["error"] == "email_already_registered"


@pytest.mark.parametrize("email", ["", "not-an-email", "a@b", "a b@example.com"])
def test_register_bad_email_is_422(client, email):
    r = register(client, email=email)
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "email"


def test_register_short_password_is_422_and_not_echoed(client):
    r = register(client, password="short")
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "password"
    assert "short" not in r.json()["detail"].replace("at least", "")


def test_password_is_stored_hashed(client):
    register(client)
    with get_connection() as conn:
        stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert PASSWORD not in stored and stored.startswith("scrypt$")


# ------------------------------------------------------------------- login
def test_login_returns_verifiable_token(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert r.headers["cache-control"] == "no-store"
    payload = security.decode_access_token(body["access_token"])
    assert payload["sub"] == body["user"]["id"]
    assert payload["exp"] - payload["iat"] == body["expires_in"]


def test_login_wrong_password_and_unknown_email_look_identical(client):
    register(client)
    wrong = login(client, password="wrong-password-1")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["error"] == "invalid_credentials"


def test_login_is_case_insensitive_on_email(client):
    register(client)
    assert login(client, email="ALICE@Example.com").status_code == 200


# ---------------------------------------------------------- protected routes
def test_protected_route_without_token_is_401(client):
    r = client.get(PROTECTED_GET)
    assert r.status_code == 401
    assert r.json()["error"] == "not_authenticated"
    assert r.headers["www-authenticate"] == "Bearer"


def test_protected_route_with_valid_token(client):
    token = token_for(client)
    r = client.get(PROTECTED_GET, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "alice@example.com"


@pytest.mark.parametrize("header", ["Basic abc", "Bearer", "token abc", "Bearer not.a.jwt"])
def test_malformed_authorization_headers_are_401(client, header):
    r = client.get(PROTECTED_GET, headers={"Authorization": header})
    assert r.status_code == 401


def test_expired_token_gives_token_expired(client):
    register(client)
    user_id = login(client).json()["user"]["id"]
    old = security.create_access_token(user_id, "user", now=datetime.now(timezone.utc) - timedelta(hours=2))
    r = client.get(PROTECTED_GET, headers=auth(old))
    assert r.status_code == 401
    assert r.json()["error"] == "token_expired"
    assert "token expired" in r.headers["www-authenticate"]


def test_tampered_token_is_rejected(client):
    token = token_for(client)
    header, payload, signature = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["role"] = "admin"
    forged_payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    r = client.get(PROTECTED_GET, headers=auth(f"{header}.{forged_payload}.{signature}"))
    assert r.status_code == 401
    assert r.json()["error"] == "invalid_token"


def test_token_signed_with_wrong_secret_is_rejected(client):
    register(client)
    user_id = login(client).json()["user"]["id"]
    now = datetime.now(timezone.utc)
    forged = jwt.encode({"sub": user_id, "role": "admin", "type": "access", "iat": now,
                         "exp": now + timedelta(minutes=5)}, "z" * 40, algorithm="HS256")
    r = client.get(PROTECTED_GET, headers=auth(forged))
    assert r.status_code == 401 and r.json()["error"] == "invalid_token"


def test_alg_none_token_is_rejected(client):
    register(client)
    user_id = login(client).json()["user"]["id"]
    now = datetime.now(timezone.utc)
    forged = jwt.encode({"sub": user_id, "type": "access", "iat": now,
                         "exp": now + timedelta(minutes=5)}, None, algorithm="none")
    r = client.get(PROTECTED_GET, headers=auth(forged))
    assert r.status_code == 401 and r.json()["error"] == "invalid_token"


def test_token_for_deleted_user_is_rejected(client):
    token = token_for(client)
    with get_connection() as conn:
        conn.execute("DELETE FROM users")
    r = client.get(PROTECTED_GET, headers=auth(token))
    assert r.status_code == 401 and r.json()["error"] == "invalid_token"


def test_role_comes_from_database_not_token(client):
    token = token_for(client)             # token says role=user
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = 'admin'")
    assert client.get(PROTECTED_GET, headers=auth(token)).json()["user"]["role"] == "admin"


# ------------------------------------- existing DNA endpoints are now protected
@pytest.mark.parametrize("path", [
    "/api/dna/analyze-sequences", "/api/dna/classify", "/api/dna/report",
    "/api/dna/report/csv", "/api/dna/report/pdf",
])
def test_dna_endpoints_require_login(client, path):
    r = client.post(path, json=BODY)
    assert r.status_code == 401
    assert r.json()["error"] == "not_authenticated"


def test_upload_requires_login(client):
    r = client.post("/api/dna/upload",
                    files={"reference_file": ("r.fa", b"ATGC"), "sample_file": ("s.fa", b"ATGA")})
    assert r.status_code == 401


def test_dna_endpoint_works_with_token(client):
    token = token_for(client)
    r = client.post("/api/dna/analyze-sequences", json=BODY, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["mutation_detected"] is True


def test_public_routes_stay_public(client):
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
