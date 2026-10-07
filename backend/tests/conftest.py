import pytest
from fastapi.testclient import TestClient

from main import app


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
