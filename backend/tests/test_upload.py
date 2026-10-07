from config import MAX_FILE_SIZE
from tests.conftest import upload


def test_valid_files(client):
    response = upload(client)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["reference"]["sequence"] == "ATGC"
    assert body["reference"]["filename"] == "ref.fasta"
    assert body["sample"]["sequence"] == "ATGA"


def test_metadata_counts_and_gc_content(client):
    body = upload(client, reference=("r.fa", b"GGCCAATT")).json()
    assert body["reference"]["metadata"] == {
        "length": 8, "A_count": 2, "T_count": 2, "G_count": 2, "C_count": 2, "GC_content": 50.0,
    }


def test_multiline_fasta_lowercase_and_crlf(client):
    content = b">seq1 description\r\natgc\r\nATGC\r\n\r\nat gc\r\n"
    body = upload(client, reference=("r.fasta", content)).json()
    assert body["reference"]["sequence"] == "ATGCATGCATGC"


def test_utf8_bom_is_accepted(client):
    response = upload(client, reference=("r.txt", b"\xef\xbb\xbfATGC"))
    assert response.status_code == 200
    assert response.json()["reference"]["sequence"] == "ATGC"


def test_missing_file_is_422(client):
    response = client.post("/api/dna/upload", files={"reference_file": ("r.fa", b"ATGC")})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["errors"][0]["field"] == "sample_file"


def test_wrong_extension_is_415(client):
    response = upload(client, reference=("r.pdf", b"ATGC"))
    assert response.status_code == 415
    assert response.json()["error"] == "unsupported_file_type"


def test_empty_file_is_400(client):
    response = upload(client, sample=("s.fa", b""))
    assert response.status_code == 400
    assert response.json()["error"] == "empty_file"


def test_header_only_file_is_400(client):
    response = upload(client, sample=("s.fa", b">only a header\n"))
    assert response.status_code == 400
    assert response.json()["error"] == "empty_file"


def test_file_too_large_is_413(client):
    big = b"A" * (MAX_FILE_SIZE + 1)
    response = upload(client, reference=("big.fa", big))
    assert response.status_code == 413
    assert response.json()["error"] == "file_too_large"


def test_file_exactly_at_size_limit_is_accepted(client, monkeypatch):
    # isolate the byte limit from the (lower) sequence-length limit
    monkeypatch.setattr("services.file_service.MAX_SEQUENCE_LENGTH", MAX_FILE_SIZE)
    response = upload(client, reference=("ok.fa", b"A" * MAX_FILE_SIZE))
    assert response.status_code == 200


def test_invalid_bases_is_422(client):
    response = upload(client, reference=("r.fa", b">x\nATGCNNXX"))
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_dna_sequence"


def test_non_utf8_file_is_400(client):
    response = upload(client, reference=("r.fa", b"\xff\xfe\x00\x80ATGC"))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_file_encoding"


def test_sequence_too_long_is_422(client, monkeypatch):
    monkeypatch.setattr("services.file_service.MAX_SEQUENCE_LENGTH", 5)
    response = upload(client, reference=("r.fa", b"ATGCATGC"))
    assert response.status_code == 422
    assert response.json()["error"] == "sequence_too_long"


def test_error_response_never_echoes_sequence_data(client):
    response = upload(client, reference=("r.fa", b"ATGCZZZ"))
    assert "ATGCZZZ" not in response.text
