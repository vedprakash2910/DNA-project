from pydantic import BaseModel, Field

from schemas.report_schemas import AnalysisRequest


class RecordCreateRequest(AnalysisRequest):
    title: str = Field(default="Untitled analysis", min_length=1, max_length=120)


class RecordSummary(BaseModel):
    id: str
    owner_id: str
    title: str
    created_at: str
    total_mutations: int
    overall_classification: str


class RecordDetail(RecordSummary):
    report: dict


class RecordResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    record: RecordDetail


class RecordListResponse(BaseModel):
    success: bool = True
    records: list[RecordSummary]
