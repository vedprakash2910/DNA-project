import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import config
from config import ALLOWED_ORIGINS, APP_VERSION
from routes.auth_routes import router as auth_router
from routes.dna_routes import router as dna_router
from routes.record_routes import router as record_router
from routes.report_routes import router as report_router
from schemas.dna import HealthResponse
from utils.exceptions import AppError, DNAAppError
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("app")

if config.JWT_SECRET_IS_EPHEMERAL:
    logger.warning(
        "JWT_SECRET is not set: using a random secret. Tokens stop working on every "
        "restart. Set JWT_SECRET (>= 32 random characters) for anything but local dev."
    )

tags_metadata = [
    {"name": "Authentication", "description": "Register, log in and get a JWT access token."},
    {"name": "DNA Analysis", "description": "Upload sequence files (multipart) and detect mutations (JSON)."},
    {"name": "Classification & Reports", "description": "Classify mutations and download JSON / CSV / PDF reports."},
    {"name": "Saved Records", "description": "Save, list, read and delete my analysis reports."},
    {"name": "System", "description": "Health and status checks (public)."},
]

app = FastAPI(
    title="DNA Sequence Mutation Detector API",
    description=(
        "Backend API for DNA Sequence Mutation Detection.\n\n"
        "**Authentication:** call `POST /api/auth/login`, copy the `access_token`, click "
        "**Authorize** and paste it. All `/api/dna/*`, `/api/records/*` and `/api/auth/me` "
        "calls then send `Authorization: Bearer <token>`.\n\n"
        "**Errors** always have the shape "
        "`{\"success\": false, \"error\": \"<code>\", \"detail\": \"<message>\"}`."
    ),
    version=APP_VERSION,
    openapi_tags=tags_metadata,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Content-Disposition"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.error("[%s] %s %s -> crashed", request_id, request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "[%s] %s %s -> %d (%.1f ms)",
        request_id, request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


def _error(status_code: int, code: str, detail: str, errors: list | None = None,
           headers: dict | None = None, extra: dict | None = None):
    body = {"success": False, "error": code, "detail": detail}
    if errors is not None:
        body["errors"] = errors
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body, headers=headers)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    logger.warning("%s %s -> %d %s: %s", request.method, request.url.path,
                   exc.status_code, exc.code, exc.message)
    # 401 errors carry a WWW-Authenticate header (class attribute `headers`).
    return _error(exc.status_code, exc.code, exc.message,
                  headers=getattr(exc, "headers", None))


@app.exception_handler(DNAAppError)
async def handle_dna_app_error(request: Request, exc: DNAAppError):
    logger.warning("%s %s -> %d %s: %s", request.method, request.url.path,
                   exc.status_code, exc.error_code, exc.message)
    # `error` = same key as every other endpoint; `error_code` kept because
    # docs/API.md and the classify/report clients already use it.
    return _error(exc.status_code, exc.error_code, exc.message,
                  extra={"error_code": exc.error_code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        location = [str(p) for p in err["loc"] if p not in ("body", "query", "path")]
        message = err["msg"].removeprefix("Value error, ")
        errors.append({"field": ".".join(location) or "request", "message": message})

    detail = "; ".join(f"{e['field']}: {e['message']}" for e in errors)
    logger.warning("%s %s -> 422 validation_error: %s", request.method, request.url.path, detail)
    return _error(422, "validation_error", detail, errors)


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    codes = {404: "not_found", 405: "method_not_allowed"}
    # keep headers such as `Allow` on a 405
    return _error(exc.status_code, codes.get(exc.status_code, "http_error"),
                  str(exc.detail), headers=getattr(exc, "headers", None))


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "internal_server_error", "Internal server error")


app.include_router(auth_router)
app.include_router(dna_router)
app.include_router(report_router)
app.include_router(record_router)


@app.get("/", tags=["System"], summary="Root message")
def home():
    return {"message": "DNA Mutation Detector Backend is running"}


@app.get("/health", tags=["System"], response_model=HealthResponse, summary="Health check")
def health():
    return {"status": "ok", "version": APP_VERSION}
