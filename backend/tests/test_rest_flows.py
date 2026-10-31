from datetime import datetime, timedelta, timezone

import jwt
import pytest

from tests.conftest import PASSWORD, auth, login, register, token_for
from utils import security

pytestmark = pytest.mark.real_auth

SEQ = {"reference": "ATGCATGC", "sample": "ATGTATGC"}
ORIGIN = "http://localhost:5173"     

PROTECTED = [
    ("get", "/api/auth/me", {}),
    ("post", "/api/dna/upload", {"files": {"reference_file": ("r.fa", b"ATGC"), "sample_file": ("s.fa", b"ATGA")}}),
    ("post", "/api/dna/analyze-sequences", {"json": SEQ}),
    ("post", "/api/dna/classify", {"json": SEQ}),
    ("post", "/api/dna/report", {"json": SEQ}),
    ("post", "/api/dna/report/csv", {"json": SEQ}),
    ("post", "/api/dna/report/pdf", {"json": SEQ}),
    ("post", "/api/records", {"json": SEQ}),
    ("get", "/api/records", {}),
    ("get", "/api/records/some-id", {}),
    ("delete", "/api/records/some-id", {}),
]


def call(client, method, path, kwargs, token=None, headers=None):
    merged = {**(auth(token) if token else {}), **(headers or {})}
    return getattr(client, method)(path, headers=merged, **kwargs)


def test_full_flow_register_login_upload_analyze_save_delete(client):
    assert register(client).status_code == 201

    logged_in = login(client)
    assert logged_in.status_code == 200
    headers = auth(logged_in.json()["access_token"])

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["user"]["email"] == "alice@example.com"


    up = client.post("/api/dna/upload", headers=headers, files={
        "reference_file": ("ref.fasta", b">ref\nATGCATGC\n"),
        "sample_file": ("sample.fasta", b">smp\nATGTATGC\n"),
    })
    assert up.status_code == 200
    ref, smp = up.json()["reference"]["sequence"], up.json()["sample"]["sequence"]

    analysis = client.post("/api/dna/analyze-sequences", headers=headers,
                           json={"reference": ref, "sample": smp})
    assert analysis.status_code == 200
    assert analysis.json()["mutations"] == [
        {"type": "Substitution", "position": 4, "original": "C", "mutated": "T"}]

    saved = client.post("/api/records", headers=headers,
                        json={"reference": ref, "sample": smp, "title": "flow"})
    assert saved.status_code == 201
    record_id = saved.json()["record"]["id"]

    assert [r["id"] for r in client.get("/api/records", headers=headers).json()["records"]] == [record_id]
    assert client.get(f"/api/records/{record_id}", headers=headers).status_code == 200

    deleted = client.delete(f"/api/records/{record_id}", headers=headers)
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get(f"/api/records/{record_id}", headers=headers).status_code == 404


@pytest.mark.parametrize("method,path,kwargs", PROTECTED)
def test_protected_endpoint_without_token_is_401(client, method, path, kwargs):
    r = call(client, method, path, kwargs)
    assert r.status_code == 401
    assert r.json()["error"] == "not_authenticated"
    assert r.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,path,kwargs", PROTECTED)
def test_protected_endpoint_with_garbage_token_is_401(client, method, path, kwargs):
    r = call(client, method, path, kwargs, token="not.a.jwt")
    assert r.status_code == 401
    assert r.json()["error"] == "invalid_token"


@pytest.mark.parametrize("method,path,kwargs", PROTECTED)
def test_valid_token_is_accepted_everywhere(client, method, path, kwargs):
    r = call(client, method, path, kwargs, token=token_for(client))
    assert r.status_code not in (401, 403)     # 404 is fine for the fake record id


def test_expired_token_is_rejected_on_a_data_endpoint(client):
    register(client)
    user_id = login(client).json()["user"]["id"]
    old = security.create_access_token(
        user_id, "user", now=datetime.now(timezone.utc) - timedelta(hours=2))
    r = client.post("/api/dna/analyze-sequences", json=SEQ, headers=auth(old))
    assert r.status_code == 401 and r.json()["error"] == "token_expired"


def test_token_signed_with_another_secret_is_rejected(client):
    register(client)
    user_id = login(client).json()["user"]["id"]
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"sub": user_id, "role": "admin", "type": "access", "iat": now, "exp": now + timedelta(minutes=5)},
        "z" * 40, algorithm="HS256")
    r = client.get("/api/records", headers=auth(forged))
    assert r.status_code == 401 and r.json()["error"] == "invalid_token"


def test_bearer_scheme_is_case_insensitive(client):
    token = token_for(client)
    r = client.get("/api/auth/me", headers={"Authorization": f"bearer {token}"})
    assert r.status_code == 200


@pytest.mark.parametrize("param", ["token", "access_token"])
def test_token_in_query_string_does_not_authenticate(client, param):
    token = token_for(client)
    assert client.get(f"/api/auth/me?{param}={token}").status_code == 401


def test_basic_auth_header_is_rejected(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Basic YWxpY2U6cHc="})
    assert r.status_code == 401


def test_login_response_headers(client):
    register(client)
    r = login(client)
    assert r.headers["content-type"].startswith("application/json")
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["x-request-id"]


def test_request_id_is_generated_and_echoed(client):
    generated = client.get("/health").headers["x-request-id"]
    assert len(generated) == 12 and generated.isalnum()
    echoed = client.get("/health", headers={"X-Request-ID": "trace-123"}).headers["x-request-id"]
    assert echoed == "trace-123"


def test_error_responses_also_carry_request_id(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.headers["x-request-id"]


def test_csv_download_headers(client):
    r = client.post("/api/dna/report/csv", json=SEQ, headers=auth(token_for(client)))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert 'filename="dna_mutation_report.csv"' in r.headers["content-disposition"]
    assert r.content.startswith(b"\xef\xbb\xbfmutation_id")


def test_pdf_download_headers(client):
    r = client.post("/api/dna/report/pdf", json=SEQ, headers=auth(token_for(client)))
    if r.status_code == 501:
        pytest.skip("reportlab not installed")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert 'filename="dna_mutation_report.pdf"' in r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")


def test_cors_preflight_allows_authorization_header(client):
    r = client.options("/api/dna/analyze-sequences", headers={
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGIN
    allowed = r.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed and "content-type" in allowed


def test_cors_header_on_normal_request_and_blocked_for_unknown_origin(client):
    ok = client.get("/health", headers={"Origin": ORIGIN})
    assert ok.headers["access-control-allow-origin"] == ORIGIN
    evil = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in evil.headers


@pytest.mark.parametrize("method,path", [
    ("get", "/api/auth/login"),
    ("post", "/api/auth/me"),
    ("get", "/api/dna/upload"),
    ("put", "/api/records"),
    ("post", "/health"),
])
def test_wrong_method_is_405_with_allow_header(client, method, path):
    r = getattr(client, method)(path)
    assert r.status_code == 405
    assert r.json()["error"] == "method_not_allowed"
    assert r.headers["allow"]


def test_unknown_record_path_with_token_is_404_json(client):
    r = client.get("/api/records/does-not-exist", headers=auth(token_for(client)))
    assert r.status_code == 404 and r.json()["error"] == "record_not_found"


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/dna/analyze-sequences", "/api/records"])
def test_malformed_json_is_422_on_every_json_endpoint(client, path):
    r = client.post(path, content="{not json", headers={
        **auth(token_for(client)), "Content-Type": "application/json"})
    assert r.status_code == 422
    assert r.json()["success"] is False


@pytest.mark.parametrize("body", [[], "text", 42, None])
def test_non_object_json_body_is_422(client, body):
    r = client.post("/api/dna/analyze-sequences", json=body, headers=auth(token_for(client)))
    assert r.status_code == 422


def test_form_encoded_body_on_json_endpoint_is_422(client):
    r = client.post("/api/dna/analyze-sequences", data=SEQ, headers=auth(token_for(client)))
    assert r.status_code == 422


def test_unknown_extra_json_fields_are_ignored(client):
    r = client.post("/api/dna/analyze-sequences", json={**SEQ, "admin": True},
                    headers=auth(token_for(client)))
    assert r.status_code == 200


def test_unicode_and_whitespace_input_is_normalised(client):
    r = client.post("/api/dna/analyze-sequences", headers=auth(token_for(client)),
                    json={"reference": ">ref\natgc\nATGC", "sample": " atgc \t ATGC "})
    assert r.status_code == 200 and r.json()["mutation_detected"] is False


def test_upload_returns_cleaned_sequences_and_metadata(client):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)), files={
        "reference_file": ("r.fa", b">x\r\natgc\r\nATGC\r\n"),
        "sample_file": ("s.txt", b"ATGA"),
    })
    assert r.status_code == 200
    body = r.json()
    assert body["reference"]["sequence"] == "ATGCATGC"
    assert body["reference"]["metadata"]["length"] == 8
    assert body["sample"]["filename"] == "s.txt"


@pytest.mark.parametrize("name", ["a.fasta", "a.fa", "a.txt", "A.FASTA"])
def test_all_allowed_extensions_are_accepted(client, name):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)), files={
        "reference_file": (name, b"ATGC"), "sample_file": (name, b"ATGC")})
    assert r.status_code == 200


@pytest.mark.parametrize("name", ["a.pdf", "a.exe", "a.fasta.sh", "noextension"])
def test_disallowed_extensions_are_415(client, name):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)), files={
        "reference_file": (name, b"ATGC"), "sample_file": ("s.fa", b"ATGC")})
    assert r.status_code == 415 and r.json()["error"] == "unsupported_file_type"


def test_path_traversal_filename_is_rejected(client):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)), files={
        "reference_file": ("../evil.fa", b"ATGC"), "sample_file": ("s.fa", b"ATGC")})
    assert r.status_code == 400 and r.json()["error"] == "invalid_filename"


def test_missing_second_file_names_the_missing_field(client):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)),
                    files={"reference_file": ("r.fa", b"ATGC")})
    assert r.status_code == 422
    assert [e["field"] for e in r.json()["errors"]] == ["sample_file"]


def test_wrong_multipart_field_names_report_both_fields(client):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)),
                    files={"file1": ("r.fa", b"ATGC"), "file2": ("s.fa", b"ATGC")})
    assert r.status_code == 422
    assert {e["field"] for e in r.json()["errors"]} == {"reference_file", "sample_file"}


def test_json_body_sent_to_multipart_endpoint_is_422(client):
    r = client.post("/api/dna/upload", json=SEQ, headers=auth(token_for(client)))
    assert r.status_code == 422


def test_plain_text_fields_instead_of_files_are_422(client):
    r = client.post("/api/dna/upload", headers=auth(token_for(client)),
                    data={"reference_file": "ATGC", "sample_file": "ATGC"})
    assert r.status_code == 422

def test_register_login_matrix(client):
    assert register(client).status_code == 201                                    
    assert register(client).status_code == 409                                    
    assert register(client, email="bad").status_code == 422                       
    assert register(client, email="b@example.com", password="short").status_code == 422
    assert login(client).status_code == 200                                      
    assert login(client, password="wrong-password-1").status_code == 401          
    assert login(client, email="ghost@example.com").status_code == 401            
    assert client.post("/api/auth/login", json={"email": "a@example.com"}).status_code == 422


def test_password_never_appears_in_any_response(client):
    for r in (register(client), login(client)):
        assert PASSWORD not in r.text
