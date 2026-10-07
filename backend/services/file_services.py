
import logging

from fastapi import UploadFile

from config import MAX_FILE_SIZE, MAX_SEQUENCE_LENGTH
from services.mutation_service import calculate_metadata
from utils.exceptions import (
    EmptyFileError,
    FileEncodingError,
    FileTooLargeError,
    InvalidDNASequenceError,
    InvalidFilenameError,
    InvalidFileTypeError,
    SequenceTooLongError,
)
from utils.fasta_parser import extract_dna_sequence
from utils.validation import (
    find_invalid_base,
    validate_file_extension,
    validate_file_size,
    validate_filename,
)

logger = logging.getLogger(__name__)


def parse_dna_file(filename: str, content: bytes) -> dict:
    """Validate raw file bytes and return {filename, sequence, metadata}."""
    if not validate_filename(filename):
        raise InvalidFilenameError("Invalid filename")

    if not validate_file_extension(filename):
        raise InvalidFileTypeError("Invalid file type. Allowed: .fasta, .fa, .txt")

    if not validate_file_size(len(content)):
        raise FileTooLargeError(
            f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    if len(content) == 0:
        raise EmptyFileError("File is empty")

    try:
        text = content.decode("utf-8-sig")  # tolerates the BOM Windows editors add
    except UnicodeDecodeError:
        raise FileEncodingError("File must be a valid UTF-8 text file") from None

    sequence = extract_dna_sequence(text)

    if not sequence:
        raise EmptyFileError("File contains no sequence data")

    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise SequenceTooLongError(
            f"Sequence is too long ({len(sequence)} bases). "
            f"Maximum is {MAX_SEQUENCE_LENGTH}"
        )

    invalid = find_invalid_base(sequence)
    if invalid:
        raise InvalidDNASequenceError(
            "Invalid DNA sequence. Only A, T, G and C are allowed."
        )

    return {
        "filename": filename,
        "sequence": sequence,
        "metadata": calculate_metadata(sequence),
    }


async def process_upload(file: UploadFile) -> dict:
  
    content = await file.read(MAX_FILE_SIZE + 1)
    result = parse_dna_file(file.filename, content)
    logger.info(
        "Parsed upload filename=%s bytes=%d bases=%d",
        file.filename, len(content), result["metadata"]["length"],
    )
    return result
