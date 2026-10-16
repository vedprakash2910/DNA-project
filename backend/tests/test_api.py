"""Endpoint tests using FastAPI's TestClient.

Needs the full requirements plus requirements-dev.txt (pytest, httpx).
Run from the backend folder:   python -m pytest tests -v
"""
import os
import sys

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from tests.sample_data import ANNOTATIONS, REFERENCE, SAMPLE  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)
BODY = {"reference": REFERENCE, "sample": SAMPLE}


def test_classify_ok():
    r = client.post("/api/dna/classify", json=BODY)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["summary"]["total_mutations"] == 4
    assert data["mutations"][0]["subtype"] == "Transition"


def test_report_json_with_annotations():
    r = client.post("/api/dna/report", json={**BODY, "annotations": ANNOTATIONS,
                                             "reference_name": "ref.fasta"})
    assert r.status_code == 200
    report = r.json()["report"]
    assert report["inputs"]["reference"]["name"] == "ref.fasta"
    assert report["mutations"][0]["annotations"][0]["name"] == "Exon 1"


def test_report_csv_download():
    r = client.post("/api/dna/report/csv", json=BODY)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    assert r.content.startswith(b"\xef\xbb\xbfmutation_id")


def test_report_pdf_download():
    r = client.post("/api/dna/report/pdf", json=BODY)
    if r.status_code == 501:
        pytest.skip("reportlab not installed")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


@pytest.mark.parametrize("path", ["classify", "report", "report/csv", "report/pdf"])
def test_invalid_base_is_400_with_error_code(path):
    r = client.post(f"/api/dna/{path}", json={"reference": "ATGX", "sample": "ATGC"})
    assert r.status_code == 400
    assert r.json()["error_code"] == "invalid_sequence"
    assert r.json()["success"] is False
    assert "position 4" in r.json()["detail"]


def test_missing_sequence_is_400():
    r = client.post("/api/dna/classify", json={"reference": "", "sample": "ATGC"})
    assert r.status_code == 400
    assert r.json()["error_code"] == "missing_sequence"


def test_missing_field_is_422_from_fastapi():
    r = client.post("/api/dna/classify", json={"reference": "ATGC"})
    assert r.status_code == 422


def test_bad_annotation_is_422():
    r = client.post("/api/dna/classify", json={
        **BODY, "annotations": [{"name": "x", "start": 10, "end": 5}]})
    assert r.status_code == 422
    assert r.json()["error_code"] == "invalid_annotation"


def test_existing_analyze_endpoint_unchanged():
    r = client.post("/api/dna/analyze-sequences", json=BODY)
    assert r.status_code == 200
    assert r.json()["message"] == "DNA analysis completed"
    assert r.json()["mutations"][0] == {
        "type": "Substitution", "position": 7, "original": "A", "mutated": "G"}
