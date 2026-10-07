from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from utils.validation import (
    validate_filename,
    validate_file_extension,
    validate_file_size,
    validate_dna_sequence
)

from utils.exceptions import (
    InvalidFilenameError,
    InvalidFileTypeError,
    FileTooLargeError,
    EmptyFileError,
    InvalidDNASequenceError
)

from utils.fasta_parser import extract_dna_sequence

from services.mutation_service import calculate_metadata, detect_mutations


router = APIRouter(
    prefix="/api/dna",
    tags=["DNA Analysis"]
)


MAX_FILE_SIZE = 5 * 1024 * 1024

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)
class SequenceRequest(BaseModel):
    reference: str
    sample: str


async def process_file(file: UploadFile):

    try:
        if not validate_filename(file.filename):
            raise InvalidFilenameError("Invalid filename")

        if not validate_file_extension(file.filename):
            raise InvalidFileTypeError(
                "Invalid file type. Allowed: .fasta, .fa, .txt"
            )

        content = await file.read()

        if not validate_file_size(len(content)):
            raise FileTooLargeError("File size exceeds 5 MB")

        if len(content) == 0:
            raise EmptyFileError("File is empty")

        temp_filename = f"{uuid4()}_{file.filename}"
        temp_path = TEMP_DIR / temp_filename

        try:
            temp_path.write_bytes(content)

            file_text = content.decode("utf-8")

            sequence = extract_dna_sequence(file_text)

            if not validate_dna_sequence(sequence):
                raise InvalidDNASequenceError(
                    "Invalid DNA sequence. Only A, T, G and C are allowed."
                )

            metadata = calculate_metadata(sequence)

            return {
                "filename": file.filename,
                "sequence": sequence,
                "metadata": metadata
            }

        finally:
            if temp_path.exists():
                temp_path.unlink()

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be a valid UTF-8 text file"
        )

    except InvalidFilenameError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except InvalidFileTypeError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileTooLargeError as error:
        raise HTTPException(
            status_code=413,
            detail=str(error)
        )

    except EmptyFileError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except InvalidDNASequenceError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/upload")
async def upload_dna(
    reference_file: UploadFile = File(...),
    sample_file: UploadFile = File(...)
):

    reference = await process_file(reference_file)
    sample = await process_file(sample_file)

    return {
        "success": True,
        "message": "DNA files processed successfully",
        "reference": reference,
        "sample": sample
    }


@router.post("/analyze-sequences")
async def analyze_sequences(data: SequenceRequest):

    reference = data.reference.upper().replace(" ", "").replace("\n", "")
    sample = data.sample.upper().replace(" ", "").replace("\n", "")

    if not reference or not sample:
        raise HTTPException(
            status_code=400,
            detail="Both reference and sample sequences are required"
        )

    if not validate_dna_sequence(reference):
        raise HTTPException(
            status_code=400,
            detail="Reference sequence can contain only A, T, G and C"
        )

    if not validate_dna_sequence(sample):
        raise HTTPException(
            status_code=400,
            detail="Sample sequence can contain only A, T, G and C"
        )

    mutations = detect_mutations(reference, sample)

    formatted_mutations = []

    for mutation in mutations:

        if mutation["type"] == "SNP":
            formatted_mutations.append({
                "type": "Substitution",
                "position": mutation["position"],
                "original": mutation["reference_base"],
                "mutated": mutation["sample_base"]
            })

        elif mutation["type"] == "Insertion":
            formatted_mutations.append({
                "type": "Insertion",
                "position": mutation["position"],
                "original": "-",
                "mutated": mutation["inserted_base"]
            })

        elif mutation["type"] == "Deletion":
            formatted_mutations.append({
                "type": "Deletion",
                "position": mutation["position"],
                "original": mutation["deleted_base"],
                "mutated": "-"
            })

    return {
        "success": True,
        "message": "DNA analysis completed",
        "mutation_detected": len(formatted_mutations) > 0,
        "mutations": formatted_mutations
    }