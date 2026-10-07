import pytest

from services.file_service import parse_dna_file
from services.mutation_service import calculate_metadata
from utils.exceptions import (
    EmptyFileError, FileEncodingError, FileTooLargeError, InvalidDNASequenceError,
    InvalidFilenameError, InvalidFileTypeError,
)
from utils.fasta_parser import extract_dna_sequence
from utils.validation import find_invalid_base, validate_dna_sequence, validate_filename


def test_extract_dna_sequence():
    assert extract_dna_sequence(">h\nat gc\n\nAT\r\n") == "ATGCAT"


def test_find_invalid_base():
    assert find_invalid_base("ATGC") is None
    assert find_invalid_base("ATNC") == (2, "N")


def test_validate_dna_sequence():
    assert validate_dna_sequence("atgc \n")
    assert not validate_dna_sequence("")
    assert not validate_dna_sequence("ATGU")


@pytest.mark.parametrize("name", ["", None, "../x.fa", "a/b.fa", "dir/x.fa"])
def test_bad_filenames(name):
    assert not validate_filename(name)


def test_metadata_empty_sequence_does_not_divide_by_zero():
    assert calculate_metadata("")["GC_content"] == 0


@pytest.mark.parametrize(
    "filename, content, exc",
    [
        ("../evil.fa", b"ATGC", InvalidFilenameError),
        ("x.exe", b"ATGC", InvalidFileTypeError),
        ("x.fa", b"", EmptyFileError),
        ("x.fa", b"ATGX", InvalidDNASequenceError),
        ("x.fa", b"\xff\xfe", FileEncodingError),
        ("x.fa", b"A" * (5 * 1024 * 1024 + 1), FileTooLargeError),
    ],
)
def test_parse_dna_file_errors(filename, content, exc):
    with pytest.raises(exc):
        parse_dna_file(filename, content)
