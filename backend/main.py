import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import ALLOWED_ORIGINS, APP_VERSION
from routes.dna_routes import router as dna_router
from schemas.dna import HealthResponse
from utils.exceptions import AppError
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("app")

tags_metadata = [
    {"name": "DNA Analysis", "description": "Upload sequence files and detect mutations."},
    {"name": "System", "description": "Health and status checks."},
]

app = FastAPI(
    title="DNA Sequence Mutation Detector API",
    description=(
        "Backend API for DNA Sequence Mutation Detection.\n\n"
        "**Errors** always have the shape "
        "`{\"success\": false, \"error\": \"<code>\", \"detail\": \"<message>\"}`."
    ),
    version=APP_VERSION,
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        # Unhandled errors are logged with a traceback by the handler below.
        logger.error("[%s] %s %s -> crashed", request_id, request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "[%s] %s %s -> %d (%.1f ms)",
        request_id, request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


def _error(status_code: int, code: str, detail: str, errors: list | None = None):
    body = {"success": False, "error": code, "detail": detail}
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    logger.warning("%s %s -> %d %s: %s", request.method, request.url.path,
                   exc.status_code, exc.code, exc.message)
    return _error(exc.status_code, exc.code, exc.message)


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
    return _error(exc.status_code, codes.get(exc.status_code, "http_error"), str(exc.detail))


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "internal_server_error", "Internal server error")


app.include_router(dna_router)


@app.get("/", tags=["System"], summary="Root message")
def home():
    return {"message": "DNA Mutation Detector Backend is running"}


@app.get("/health", tags=["System"], response_model=HealthResponse, summary="Health check")
def health():
    return {"status": "ok", "version": APP_VERSION}
