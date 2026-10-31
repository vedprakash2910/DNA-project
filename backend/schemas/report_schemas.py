from typing import List

from pydantic import BaseModel, Field


class AnnotationRegion(BaseModel):
    """A named region on the reference sequence (1-based, inclusive)."""
    name: str
    start: int
    end: int
    feature_type: str = "region"


class AnalysisRequest(BaseModel):
    reference: str
    sample: str
    reference_name: str = Field(default="reference", max_length=100)
    sample_name: str = Field(default="sample", max_length=100)
    annotations: List[AnnotationRegion] = Field(default_factory=list)

class ClassificationResponse(BaseModel):
    """Body of POST /api/dna/classify."""
    success: bool = True
    message: str
    mutation_detected: bool
    summary: dict
    mutations: list[dict]


class ReportResponse(BaseModel):
    """Body of POST /api/dna/report."""
    success: bool = True
    message: str
    report: dict
