from fastapi import APIRouter, Response

from schemas.report_schemas import AnalysisRequest
from services.report_service import (
    analyze_pair,
    build_report,
    classification_response,
    report_response,
    report_to_csv,
    report_to_pdf,
)

router = APIRouter(
    prefix="/api/dna",
    tags=["Classification & Reports"]
)

ERROR_RESPONSES = {
    400: {"description": "Missing or invalid sequence"},
    413: {"description": "Sequence too long"},
    422: {"description": "Invalid request body or annotation"},
    500: {"description": "Report generation failed"},
}


def _run(data: AnalysisRequest):
    regions = [region.model_dump() for region in data.annotations]
    return analyze_pair(data.reference, data.sample, regions)


def _download(content, media_type, filename):
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/classify", responses=ERROR_RESPONSES)
def classify(data: AnalysisRequest):
    """Detect mutations and classify each one (SNP/Indel, transition/transversion)."""
    return classification_response(_run(data))


@router.post("/report", responses=ERROR_RESPONSES)
def report(data: AnalysisRequest):
    """Full report as JSON: inputs, summary, classified + annotated mutations."""
    analysis = _run(data)
    return report_response(
        build_report(analysis, data.reference_name, data.sample_name)
    )


@router.post("/report/csv", responses={**ERROR_RESPONSES, 200: {"content": {"text/csv": {}}}})
def report_csv(data: AnalysisRequest):
    """Same report as a CSV download (one row per mutation)."""
    analysis = _run(data)
    csv_text = report_to_csv(build_report(analysis, data.reference_name, data.sample_name))
    # utf-8-sig adds a BOM so Excel reads non-ASCII annotation names correctly
    return _download(csv_text.encode("utf-8-sig"), "text/csv; charset=utf-8",
                     "dna_mutation_report.csv")


@router.post("/report/pdf", responses={**ERROR_RESPONSES, 200: {"content": {"application/pdf": {}}},
                                       501: {"description": "reportlab is not installed"}})
def report_pdf(data: AnalysisRequest):
    """Same report as a PDF download."""
    analysis = _run(data)
    pdf_bytes = report_to_pdf(build_report(analysis, data.reference_name, data.sample_name))
    return _download(pdf_bytes, "application/pdf", "dna_mutation_report.pdf")
