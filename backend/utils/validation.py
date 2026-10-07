from pathlib import Path


ALLOWED_EXTENSIONS = {".fasta", ".fa", ".txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


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


def validate_dna_sequence(sequence):
    sequence = sequence.upper().replace("\n", "").replace("\r", "").replace(" ", "")

    if not sequence:
        return False

    allowed_bases = set("ATGC")

    return all(base in allowed_bases for base in sequence)