from fastapi import APIRouter, Depends, Response

from dependencies import get_current_user
from schemas.dna import ErrorResponse
from schemas.record_schemas import RecordCreateRequest, RecordListResponse, RecordResponse
from services import record_service
from services.report_service import analyze_pair, build_report

router = APIRouter(
    prefix="/api/records",
    tags=["Saved Records"],
    dependencies=[Depends(get_current_user)],  # every route here needs a valid token
)

_ERRORS = {
    401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"},
    403: {"model": ErrorResponse, "description": "Record belongs to another user"},
    404: {"model": ErrorResponse, "description": "Record not found"},
}


@router.post(
    "",
    status_code=201,
    response_model=RecordResponse,
    summary="Run an analysis and save the report as one of my records",
    responses={401: _ERRORS[401]},
)
def create_record(data: RecordCreateRequest, current_user: dict = Depends(get_current_user)):
    regions = [region.model_dump() for region in data.annotations]
    analysis = analyze_pair(data.reference, data.sample, regions)
    report = build_report(analysis, data.reference_name, data.sample_name)
    record = record_service.create_record(current_user["id"], data.title, report)
    return {"success": True, "message": "Record saved", "record": record}


@router.get(
    "",
    response_model=RecordListResponse,
    summary="List my records (admins see everyone's)",
    responses={401: _ERRORS[401]},
)
def list_records(current_user: dict = Depends(get_current_user)):
    return {"success": True, "records": record_service.list_records(current_user)}


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get one record (owner or admin only)",
    responses=_ERRORS,
)
def get_record(record_id: str, current_user: dict = Depends(get_current_user)):
    record = record_service.get_authorized_record(record_id, current_user)
    return {"success": True, "message": "OK", "record": record}


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Delete one record (owner or admin only)",
    responses=_ERRORS,
)
def delete_record(record_id: str, current_user: dict = Depends(get_current_user)):
    record_service.delete_record(record_id, current_user)
    return Response(status_code=204)
