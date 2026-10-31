import pytest

import config
from schemas.auth_schemas import MeResponse, RegisterResponse, TokenResponse
from schemas.dna import AnalysisResponse, ErrorResponse, HealthResponse, UploadResponse
from schemas.record_schemas import RecordListResponse, RecordResponse
from schemas.report_schemas import ClassificationResponse, ReportResponse
from tests.conftest import auth, token_for, upload

OPERATIONS = [
    ("get", "/", False),
    ("get", "/health", False),
    ("post", "/api/auth/register", False),
    ("post", "/api/auth/login", False),
    ("get", "/api/auth/me", True),
    ("post", "/api/dna/upload", True),
    ("post", "/api/dna/analyze-sequences", True),
    ("post", "/api/dna/classify", True),
    ("post", "/api/dna/report", True),
    ("post", "/api/dna/report/csv", True),
    ("post", "/api/dna/report/pdf", True),
    ("post", "/api/records", True),
    ("get", "/api/records", True),
    ("get", "/api/records/{record_id}", True),
    ("delete", "/api/records/{record_id}", True),
]

DOCUMENTED_CODES = {
    ("post", "/api/auth/register"): {"201", "409", "422"},
    ("post", "/api/auth/login"): {"200", "401", "422"},
    ("get", "/api/auth/me"): {"200", "401"},
    ("post", "/api/dna/upload"): {"200", "400", "401", "413", "415", "422", "500"},
    ("post", "/api/dna/analyze-sequences"): {"200", "401", "422", "500"},
    ("post", "/api/dna/classify"): {"200", "400", "401", "413", "422", "500"},
    ("post", "/api/dna/report"): {"200", "400", "401", "413", "422", "500"},
    ("post", "/api/dna/report/csv"): {"200", "400", "401", "422"},
    ("post", "/api/dna/report/pdf"): {"200", "400", "401", "422", "501"},
    ("post", "/api/records"): {"201", "401", "422"},
    ("get", "/api/records"): {"200", "401"},
    ("get", "/api/records/{record_id}"): {"200", "401", "403", "404"},
    ("delete", "/api/records/{record_id}"): {"204", "401", "403", "404"},
}

SEQ = {"reference": "ATGCATGC", "sample": "ATGTATGC"}


@pytest.fixture()
def spec(client):
    return client.get("/openapi.json").json()


def test_swagger_ui_and_redoc_are_served_as_html(client):
    for path in ("/docs", "/redoc"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")


def test_openapi_document_is_valid_json_with_metadata(client, spec):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] and spec["info"]["version"] == config.APP_VERSION


@pytest.mark.parametrize("method,path,needs_login", OPERATIONS)
def test_every_operation_is_documented(spec, method, path, needs_login):
    assert path in spec["paths"], f"{path} missing from OpenAPI"
    operation = spec["paths"][path][method]
    assert operation["summary"], f"{method.upper()} {path} has no summary"
    assert operation["tags"], f"{method.upper()} {path} has no tag"


@pytest.mark.parametrize("method,path,needs_login", OPERATIONS)
def test_security_requirement_matches_access_rules(spec, method, path, needs_login):
    operation = spec["paths"][path][method]
    assert bool(operation.get("security")) is needs_login


def test_bearer_security_scheme_is_declared(spec):
    schemes = spec["components"]["securitySchemes"].values()
    assert any(s.get("type") == "http" and s.get("scheme") == "bearer" for s in schemes)


@pytest.mark.parametrize("key,codes", DOCUMENTED_CODES.items(), ids=lambda v: str(v))
def test_documented_status_codes(spec, key, codes):
    method, path = key
    assert codes <= set(spec["paths"][path][method]["responses"])


def _resolve(spec, schema):
    if "$ref" in schema:
        node = spec
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return node
    return schema


def test_upload_is_documented_as_multipart_with_two_required_files(spec):
    body = spec["paths"]["/api/dna/upload"]["post"]["requestBody"]
    assert body["required"] is True
    form = _resolve(spec, body["content"]["multipart/form-data"]["schema"])
    assert {"reference_file", "sample_file"} <= set(form["properties"])
    assert {"reference_file", "sample_file"} <= set(form["required"])


@pytest.mark.parametrize("path", [
    "/api/auth/register", "/api/auth/login", "/api/dna/analyze-sequences",
    "/api/dna/classify", "/api/dna/report", "/api/records",
])
def test_json_endpoints_declare_json_request_body(spec, path):
    assert "application/json" in spec["paths"][path]["post"]["requestBody"]["content"]


def test_error_responses_reference_the_standard_error_schema(spec):
    responses = spec["paths"]["/api/dna/analyze-sequences"]["post"]["responses"]
    ref = responses["401"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("/ErrorResponse")



def test_public_endpoint_schemas(client):
    HealthResponse.model_validate(client.get("/health").json())


def test_auth_response_schemas(client):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "correct-horse-1"})
    assert r.status_code == 201
    RegisterResponse.model_validate(r.json())

    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "correct-horse-1"})
    assert r.status_code == 200
    TokenResponse.model_validate(r.json())

    me = client.get("/api/auth/me", headers=auth(r.json()["access_token"]))
    assert me.status_code == 200
    MeResponse.model_validate(me.json())


def test_dna_response_schemas(client):
    up = upload(client)
    assert up.status_code == 200
    UploadResponse.model_validate(up.json())

    analyze = client.post("/api/dna/analyze-sequences", json=SEQ)
    assert analyze.status_code == 200
    model = AnalysisResponse.model_validate(analyze.json())
    assert model.mutation_count == len(model.mutations) == 1

    classify = client.post("/api/dna/classify", json=SEQ)
    ClassificationResponse.model_validate(classify.json())

    report = client.post("/api/dna/report", json=SEQ)
    ReportResponse.model_validate(report.json())


@pytest.mark.real_auth
def test_record_response_schemas(client):
    headers = auth(token_for(client))
    created = client.post("/api/records", json={**SEQ, "title": "t"}, headers=headers)
    assert created.status_code == 201
    RecordResponse.model_validate(created.json())

    record_id = created.json()["record"]["id"]
    RecordResponse.model_validate(client.get(f"/api/records/{record_id}", headers=headers).json())
    RecordListResponse.model_validate(client.get("/api/records", headers=headers).json())

NEGATIVE_CASES = [
    ("post", "/api/dna/analyze-sequences", {"json": {"reference": "ATGX", "sample": "ATGC"}}, 422),
    ("post", "/api/dna/analyze-sequences", {"json": {"reference": "ATGC"}}, 422),
    ("post", "/api/dna/classify", {"json": {"reference": "ATGX", "sample": "ATGC"}}, 400),
    ("post", "/api/dna/classify", {"json": {"reference": "", "sample": "ATGC"}}, 400),
    ("post", "/api/dna/classify", {"json": {**SEQ, "annotations": [{"name": "x", "start": 5, "end": 2}]}}, 422),
    ("post", "/api/dna/upload", {"files": {"reference_file": ("r.pdf", b"ATGC"), "sample_file": ("s.fa", b"ATGC")}}, 415),
    ("post", "/api/dna/upload", {"files": {"reference_file": ("r.fa", b"")}}, 422),
    ("get", "/nope", {}, 404),
    ("get", "/api/dna/analyze-sequences", {}, 405),
]


@pytest.mark.parametrize("method,path,kwargs,status", NEGATIVE_CASES)
def test_every_error_uses_the_standard_error_schema(client, method, path, kwargs, status):
    r = getattr(client, method)(path, **kwargs)
    assert r.status_code == status
    assert r.headers["content-type"].startswith("application/json")
    body = ErrorResponse.model_validate(r.json())
    assert body.success is False and body.error and body.detail
