def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_id_header_is_returned(client):
    assert client.get("/health").headers["X-Request-ID"]
    assert client.get("/health", headers={"X-Request-ID": "abc"}).headers["X-Request-ID"] == "abc"


def test_unknown_route_uses_standard_error_shape(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"] == "not_found"


def test_wrong_method_is_405(client):
    response = client.get("/api/dna/analyze-sequences")
    assert response.status_code == 405
    assert response.json()["error"] == "method_not_allowed"


def test_swagger_and_openapi_are_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200

    schema = client.get("/openapi.json").json()
    assert "/api/dna/upload" in schema["paths"]
    assert "/api/dna/analyze-sequences" in schema["paths"]

    analyze = schema["paths"]["/api/dna/analyze-sequences"]["post"]
    assert analyze["summary"]
    assert {"200", "422", "500"} <= set(analyze["responses"])

    upload = schema["paths"]["/api/dna/upload"]["post"]
    assert {"200", "400", "413", "415", "422", "500"} <= set(upload["responses"])
