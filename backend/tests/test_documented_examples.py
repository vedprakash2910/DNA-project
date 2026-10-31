import json
import os

import pytest

from tests.conftest import auth

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "sample_outputs")

# Values that differ on every run: compared by presence only.
VOLATILE_KEYS = {"id", "owner_id", "created_at", "access_token", "report_id", "generated_at"}
# A saved record embeds the whole report; only its presence is checked there.
RECORD_KEYS = VOLATILE_KEYS | {"report"}


def load(name):
    with open(os.path.join(DOCS, name), encoding="utf-8") as f:
        return json.load(f)


def mask(value, keys=VOLATILE_KEYS):
    if isinstance(value, dict):
        return {k: ("<masked>" if k in keys else mask(v, keys)) for k, v in value.items()}
    if isinstance(value, list):
        return [mask(v, keys) for v in value]
    return value


def test_classify_example_matches_real_response(client):
    request = load("request.json")
    r = client.post("/api/dna/classify", json=request)
    assert r.status_code == 200
    assert r.json() == load("classify_response.json")


def test_report_example_matches_real_response(client):
    request = load("request.json")
    r = client.post("/api/dna/report", json=request)
    assert r.status_code == 200
    assert mask(r.json()) == mask(load("report_response.json"))


@pytest.mark.parametrize("name,payload", [
    ("missing_sequence", {"reference": "", "sample": "ATGC"}),
    ("invalid_sequence", {"reference": "ATGX", "sample": "ATGC"}),
    ("annotation_out_of_range", {"reference": "ATGC", "sample": "ATGC",
                                  "annotations": [{"name": "Gene", "start": 2, "end": 99}]}),
])
def test_error_examples_match_real_responses(client, name, payload):
    documented = load("error_examples.json")[name]
    r = client.post("/api/dna/classify", json=payload)
    assert r.status_code == documented["http_status"]
    for key, value in documented["body"].items():       
        assert r.json()[key] == value


@pytest.mark.real_auth
def test_rest_examples_replay_in_order(client):
    """docs/sample_outputs/rest_examples.json is replayed top to bottom."""
    examples = {k: v for k, v in load("rest_examples.json").items() if not k.startswith("_")}
    token = None

    for name, example in examples.items():
        request = example["request"]
        kwargs = {}
        if "json" in request:
            kwargs["json"] = request["json"]
        if "files" in request:
            kwargs["files"] = {
                field: (f["filename"], f["content"].encode("utf-8"))
                for field, f in request["files"].items()
            }
        if request.get("auth"):
            kwargs["headers"] = auth(token)

        response = getattr(client, request["method"].lower())(request["path"], **kwargs)

        assert response.status_code == example["status"], f"{name}: {response.text}"
        assert mask(response.json(), RECORD_KEYS) == mask(example["response"], RECORD_KEYS), name

        if name == "login":
            token = response.json()["access_token"]
