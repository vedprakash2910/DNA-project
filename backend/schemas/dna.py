from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import MAX_SEQUENCE_LENGTH
from utils.fasta_parser import extract_dna_sequence
from utils.validation import find_invalid_base


# ----------------------------------------------------------------- requests
class SequenceRequest(BaseModel):
    """Two raw sequences to compare. Input is normalised before validation:
    FASTA headers are dropped, whitespace removed, letters upper-cased."""

    reference: str = Field(
        ...,
        description="Reference DNA sequence (A, T, G, C). FASTA text is accepted.",
    )
    sample: str = Field(
        ...,
        description="Sample DNA sequence to compare against the reference.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"reference": "ATGCATGC", "sample": "ATGTATGC"}
        }
    )

    @field_validator("reference", "sample")
    @classmethod
    def clean_and_validate(cls, value: str) -> str:
        sequence = extract_dna_sequence(value)

        if not sequence:
            raise ValueError("Sequence must not be empty")

        if len(sequence) > MAX_SEQUENCE_LENGTH:
            raise ValueError(
                f"Sequence is too long ({len(sequence)} bases). "
                f"Maximum is {MAX_SEQUENCE_LENGTH}"
            )

        invalid = find_invalid_base(sequence)
        if invalid:
            index, base = invalid
            raise ValueError(
                f"Can contain only A, T, G and C (found '{base}' at position {index + 1})"
            )

        return sequence


# ---------------------------------------------------------------- responses
class SequenceMetadata(BaseModel):
    length: int
    A_count: int
    T_count: int
    G_count: int
    C_count: int
    GC_content: float = Field(..., description="Percentage of G + C bases")


class ParsedSequence(BaseModel):
    filename: str
    sequence: str
    metadata: SequenceMetadata


class UploadResponse(BaseModel):
    success: bool = True
    message: str = "DNA files processed successfully"
    reference: ParsedSequence
    sample: ParsedSequence


class Mutation(BaseModel):
    type: Literal["Substitution", "Insertion", "Deletion"]
    position: int = Field(..., ge=1, description="1-based position in the reference")
    original: str = Field(..., description="Reference base, '-' for an insertion")
    mutated: str = Field(..., description="Sample base, '-' for a deletion")


class MutationSummary(BaseModel):
    substitutions: int = 0
    insertions: int = 0
    deletions: int = 0


class AnalysisResponse(BaseModel):
    success: bool = True
    message: str = "DNA analysis completed"
    mutation_detected: bool
    mutation_count: int
    summary: MutationSummary
    mutations: list[Mutation]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "DNA analysis completed",
                "mutation_detected": True,
                "mutation_count": 1,
                "summary": {"substitutions": 1, "insertions": 0, "deletions": 0},
                "mutations": [
                    {"type": "Substitution", "position": 4, "original": "C", "mutated": "T"}
                ],
            }
        }
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    """Every error from this API has this shape."""

    success: bool = False
    error: str = Field(..., description="Stable machine-readable error code")
    detail: str = Field(..., description="Human-readable message, safe to show in the UI")
    errors: list[dict] | None = Field(
        None, description="Per-field problems (only for request validation errors)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "invalid_dna_sequence",
                "detail": "Invalid DNA sequence. Only A, T, G and C are allowed.",
            }
        }
    )
