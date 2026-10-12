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

<<<<<<< HEAD

def validate_sequence_length(sequence: str) -> bool:
    return len(sequence) <= MAX_SEQUENCE_LENGTH
=======
    return all(base in allowed_bases for base in sequence)


    # ---------------------------------------------------------------------------
# Validation for the classification / report endpoints (JSON request bodies)
# ---------------------------------------------------------------------------
MAX_SEQUENCE_LENGTH = 1_000_000  # bases, per sequence
MAX_ANNOTATIONS = 1000


def normalize_sequence(raw):
    """Upper-case a pasted sequence, drop FASTA header lines and ALL whitespace."""
    if raw is None:
        return ""
    lines = [
        line for line in str(raw).splitlines()
        if not line.lstrip().startswith(">")
    ]
    return "".join("".join(lines).split()).upper()


def find_invalid_base(sequence):
    """Return (character, 1-based position) of the first non-ATGC base, or None."""
    allowed = set("ATGC")
    for index, base in enumerate(sequence, start=1):
        if base not in allowed:
            return base, index
    return None


def validate_sequence_pair(reference, sample):
    """Normalise and validate a reference/sample pair. Returns (reference, sample)."""
    reference = normalize_sequence(reference)
    sample = normalize_sequence(sample)

    if not reference or not sample:
        raise MissingSequenceError("Both reference and sample sequences are required")

    for label, sequence in (("Reference", reference), ("Sample", sample)):
        if len(sequence) > MAX_SEQUENCE_LENGTH:
            raise SequenceTooLongError(
                f"{label} sequence is too long ({len(sequence)} bases). "
                f"Maximum allowed is {MAX_SEQUENCE_LENGTH} bases."
            )
        invalid = find_invalid_base(sequence)
        if invalid:
            base, position = invalid
            raise InvalidSequenceError(
                f"{label} sequence contains invalid character '{base}' at "
                f"position {position}. Only A, T, G and C are allowed."
            )

    return reference, sample


def validate_annotation_regions(regions, reference_length):
    """Check annotation regions against the reference. Returns a cleaned list."""
    if len(regions) > MAX_ANNOTATIONS:
        raise InvalidAnnotationError(
            f"Too many annotations ({len(regions)}). Maximum is {MAX_ANNOTATIONS}."
        )

    cleaned = []
    for index, region in enumerate(regions, start=1):
        name = str(region.get("name", "")).strip()
        start = region.get("start")
        end = region.get("end")
        feature_type = str(region.get("feature_type") or "region").strip() or "region"

        if not name:
            raise InvalidAnnotationError(f"Annotation #{index} must have a name")
        if not isinstance(start, int) or not isinstance(end, int):
            raise InvalidAnnotationError(
                f"Annotation '{name}' must have integer start and end positions"
            )
        if start < 1 or end < start:
            raise InvalidAnnotationError(
                f"Annotation '{name}' is invalid: start must be >= 1 and end must be >= start"
            )
        if end > reference_length:
            raise InvalidAnnotationError(
                f"Annotation '{name}' ends at {end}, beyond the reference length "
                f"({reference_length})"
            )

        cleaned.append(
            {"name": name, "feature_type": feature_type, "start": start, "end": end}
        )

    return cleaned
>>>>>>> 0167eaf (Add validation, error classes and report wiring)
