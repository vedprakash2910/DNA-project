
from fastapi import APIRouter, File, UploadFile

from schemas.dna import AnalysisResponse, ErrorResponse, SequenceRequest, UploadResponse
from services import analysis_service, file_service

router = APIRouter(prefix="/api/dna", tags=["DNA Analysis"])

_ERRORS = {
    400: {"model": ErrorResponse, "description": "Invalid filename, empty file or non-UTF-8 file"},
    413: {"model": ErrorResponse, "description": "File larger than the upload limit"},
    415: {"model": ErrorResponse, "description": "File extension not allowed"},
    422: {"model": ErrorResponse, "description": "Invalid DNA sequence or malformed request"},
    500: {"model": ErrorResponse, "description": "Unexpected server / engine error"},
}


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload reference and sample files",
    description=(
        "Accepts two FASTA / text files (`.fasta`, `.fa`, `.txt`, max 5 MB each), "
        "validates them and returns the cleaned sequences with base counts and GC content. "
        "Use the returned sequences with `POST /api/dna/analyze-sequences`."
    ),
    responses={k: _ERRORS[k] for k in (400, 413, 415, 422, 500)},
)
async def upload_dna(
    reference_file: UploadFile = File(..., description="Reference sequence file"),
    sample_file: UploadFile = File(..., description="Sample sequence file"),
):
    reference = await file_service.process_upload(reference_file)
    sample = await file_service.process_upload(sample_file)

    return {
        "success": True,
        "message": "DNA files processed successfully",
        "reference": reference,
        "sample": sample,
    }

@router.post(
    "/analyze-sequences",
    response_model=AnalysisResponse,
    summary="Detect mutations between two sequences",
    description=(
        "Compares `sample` against `reference` and returns substitutions, "
        "insertions and deletions with 1-based positions in the reference. "
        "Input is normalised first (upper-cased, whitespace and FASTA headers removed)."
    ),
    responses={k: _ERRORS[k] for k in (422, 500)},
)
def analyze_sequences(data: SequenceRequest):
    return analysis_service.analyze(data.reference, data.sample)
