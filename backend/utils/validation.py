from pathlib import Path

from config import MAX_FILE_SIZE, MAX_SEQUENCE_LENGTH

ALLOWED_EXTENSIONS = {".fasta", ".fa", ".txt"}
ALLOWED_BASES = frozenset("ATGC")


def validate_filename(filename):
    if not filename:
        return False

    name = Path(filename).name

    if name != filename:
        return False

    return True


def validate_file_extension(filename):
    extension = Path(filename).suffix.lower()
    return extension in ALLOWED_EXTENSIONS


def validate_file_size(file_size):
    return file_size <= MAX_FILE_SIZE


def find_invalid_base(sequence: str):
    """Return (index, character) of the first non-ATGC character, or None."""
    for index, base in enumerate(sequence.upper()):
        if base not in ALLOWED_BASES:
            return index, base
    return None


def validate_dna_sequence(sequence):
    sequence = "".join(sequence.upper().split())

    if not sequence:
        return False

    return find_invalid_base(sequence) is None


def validate_sequence_length(sequence: str) -> bool:
    return len(sequence) <= MAX_SEQUENCE_LENGTH
