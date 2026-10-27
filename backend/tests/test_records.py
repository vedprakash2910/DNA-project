
"""HTTP tests for record authorization (owner / other user / admin).

Run:  python -m pytest tests/test_records.py -v
"""
import pytest

from tests.conftest import auth, token_for
from utils.database import get_connection

pytestmark = pytest.mark.real_auth

BODY = {"reference": "ATGCATGC", "sample": "ATGTATGC", "title": "demo"}


def create(client, token, **extra):
    return client.post("/api/records", json={**BODY, **extra}, headers=auth(token))


@pytest.fixture()
def alice(client):
    return token_for(client, "alice@example.com")


@pytest.fixture()
def bob(client):
    return token_for(client, "bob@example.com")


def test_records_require_login(client):
    assert client.get("/api/records").status_code == 401
    assert client.post("/api/records", json=BODY).status_code == 401
    assert client.get("/api/records/anything").status_code == 401
    assert client.delete("/api/records/anything").status_code == 401


def test_create_and_read_own_record(client, alice):
    r = create(client, alice)
    assert r.status_code == 201
    record = r.json()["record"]
    assert record["title"] == "demo"
    assert record["total_mutations"] == 1
    got = client.get(f"/api/records/{record['id']}", headers=auth(alice))
    assert got.status_code == 200
    assert got.json()["record"]["report"]["summary"]["total_mutations"] == 1


def test_invalid_sequence_is_rejected_and_nothing_saved(client, alice):
    r = client.post("/api/records", json={"reference": "ATGX", "sample": "ATGC"}, headers=auth(alice))
    assert r.status_code == 400
    assert client.get("/api/records", headers=auth(alice)).json()["records"] == []


def test_list_shows_only_my_records(client, alice, bob):
    create(client, alice, title="alice-1")
    create(client, bob, title="bob-1")
    titles = [r["title"] for r in client.get("/api/records", headers=auth(alice)).json()["records"]]
    assert titles == ["alice-1"]


def test_other_user_gets_403_on_read_and_delete(client, alice, bob):
    record_id = create(client, alice).json()["record"]["id"]
    read = client.get(f"/api/records/{record_id}", headers=auth(bob))
    assert read.status_code == 403 and read.json()["error"] == "forbidden"
    assert client.delete(f"/api/records/{record_id}", headers=auth(bob)).status_code == 403
    assert client.get(f"/api/records/{record_id}", headers=auth(alice)).status_code == 200


def test_owner_can_delete(client, alice):
    record_id = create(client, alice).json()["record"]["id"]
    assert client.delete(f"/api/records/{record_id}", headers=auth(alice)).status_code == 204
    assert client.get(f"/api/records/{record_id}", headers=auth(alice)).status_code == 404


def test_unknown_record_is_404(client, alice):
    r = client.get("/api/records/does-not-exist", headers=auth(alice))
    assert r.status_code == 404 and r.json()["error"] == "record_not_found"


def test_admin_can_read_list_and_delete_any_record(client, alice):
    record_id = create(client, alice).json()["record"]["id"]
    admin = token_for(client, "root@example.com")
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = 'admin' WHERE email = 'root@example.com'")
    assert client.get(f"/api/records/{record_id}", headers=auth(admin)).status_code == 200
    assert len(client.get("/api/records", headers=auth(admin)).json()["records"]) == 1
    assert client.delete(f"/api/records/{record_id}", headers=auth(admin)).status_code == 204
