import pytest

URL = "/api/dna/analyze-sequences"


def analyze(client, reference, sample):
    return client.post(URL, json={"reference": reference, "sample": sample})


# --------------------------------------------------------- happy paths
def test_identical_sequences_have_no_mutations(client):
    body = analyze(client, "ATGCATGC", "ATGCATGC").json()
    assert body["success"] is True
    assert body["mutation_detected"] is False
    assert body["mutation_count"] == 0
    assert body["mutations"] == []


def test_substitution(client):
    body = analyze(client, "ATGCATGC", "ATGTATGC").json()
    assert body["mutation_detected"] is True
    assert body["mutations"] == [
        {"type": "Substitution", "position": 4, "original": "C", "mutated": "T"}
    ]
    assert body["summary"] == {"substitutions": 1, "insertions": 0, "deletions": 0}


def test_insertion(client):
    body = analyze(client, "ATGC", "ATGGC").json()
    assert body["mutations"] == [
        {"type": "Insertion", "position": 4, "original": "-", "mutated": "G"}
    ]
    assert body["summary"]["insertions"] == 1


def test_deletion(client):
    body = analyze(client, "ATGC", "ATC").json()
    assert body["mutations"] == [
        {"type": "Deletion", "position": 3, "original": "G", "mutated": "-"}
    ]
    assert body["summary"]["deletions"] == 1


# ------------------------------------------------------ input normalising
def test_input_is_normalised(client):
    body = analyze(client, ">ref\natgc\nATGC", "  ATGC \t atgc\r\n").json()
    assert body["mutation_detected"] is False


def test_engine_receives_normalised_sequences(client, monkeypatch):
    seen = {}

    def spy(reference, sample):
        seen["args"] = (reference, sample)
        return []

    monkeypatch.setattr("services.mutation_service.detect_mutations", spy)
    assert analyze(client, "at gc", ">h\nAT\nGA").status_code == 200
    assert seen["args"] == ("ATGC", "ATGA")


# ------------------------------------------------------ request validation
@pytest.mark.parametrize("field", ["reference", "sample"])
def test_empty_sequence_is_422(client, field):
    payload = {"reference": "ATGC", "sample": "ATGC", field: "   "}
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["errors"][0]["field"] == field


@pytest.mark.parametrize("field", ["reference", "sample"])
def test_invalid_bases_name_the_field_and_position(client, field):
    payload = {"reference": "ATGC", "sample": "ATGC", field: "ATXC"}
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    error = response.json()["errors"][0]
    assert error["field"] == field
    assert "'X'" in error["message"] and "position 3" in error["message"]


def test_missing_field_is_422(client):
    response = client.post(URL, json={"reference": "ATGC"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "sample"


def test_wrong_type_is_422(client):
    assert client.post(URL, json={"reference": 123, "sample": "ATGC"}).status_code == 422


def test_malformed_json_is_422(client):
    response = client.post(URL, content="{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_sequence_too_long_is_422(client, monkeypatch):
    monkeypatch.setattr("schemas.dna.MAX_SEQUENCE_LENGTH", 5)
    response = analyze(client, "ATGCATGC", "ATGC")
    assert response.status_code == 422
    assert "too long" in response.json()["detail"]


# ---------------------------------------------------- engine failure paths
def test_engine_crash_returns_500_without_leaking_internals(client, monkeypatch):
    def boom(reference, sample):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("services.mutation_service.detect_mutations", boom)
    response = analyze(client, "ATGC", "ATGA")
    assert response.status_code == 500
    assert response.json()["error"] == "engine_error"
    assert "secret" not in response.text


def test_engine_returning_unknown_mutation_type_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "services.mutation_service.detect_mutations",
        lambda r, s: [{"type": "Inversion", "position": 1}],
    )
    response = analyze(client, "ATGC", "ATGA")
    assert response.status_code == 500
    assert response.json()["error"] == "engine_error"


def test_bug_outside_engine_returns_generic_500(client, monkeypatch):
    # A bug in the service layer (not the engine wrapper) must still give the standard 500 shape.
    monkeypatch.setattr("routes.dna_routes.analysis_service.analyze", lambda r, s: 1 / 0)
    response = analyze(client, "ATGC", "ATGA")
    assert response.status_code == 500
    assert response.json() == {
        "success": False, "error": "internal_server_error", "detail": "Internal server error",
    }


# ------------------------------------------- known engine limitation (not API)
@pytest.mark.xfail(
    strict=True,
    reason="Engine heuristic misreads ACGT->AGGT as Deletion+Insertion instead of one "
           "Substitution. Remove this marker once the algorithm is fixed.",
)
def test_single_substitution_followed_by_matching_base(client):
    body = analyze(client, "ACGT", "AGGT").json()
    assert body["mutations"] == [
        {"type": "Substitution", "position": 2, "original": "C", "mutated": "G"}
    ]
