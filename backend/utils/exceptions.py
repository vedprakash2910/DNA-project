
class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.__name__
        super().__init__(self.message)


class InvalidFilenameError(AppError):
    status_code = 400
    code = "invalid_filename"


class InvalidFileTypeError(AppError):
    status_code = 415
    code = "unsupported_file_type"


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"

class EmptyFileError(AppError):
    status_code = 400
    code = "empty_file"


class FileEncodingError(AppError):
    status_code = 400
    code = "invalid_file_encoding"


class InvalidDNASequenceError(AppError):
    status_code = 422
    code = "invalid_dna_sequence"


class SequenceTooLongError(AppError):
    status_code = 422
    code = "sequence_too_long"


class EngineError(AppError):
    """The algorithm engine failed or returned something unexpected."""

    status_code = 500
    code = "engine_error"

class InvalidDNASequenceError(Exception):
    pass


# ---------------------------------------------------------------------------
# Errors for the classification / report endpoints.
# They share one base class so main.py can turn all of them into a
# consistent JSON error response with a single handler.
# ---------------------------------------------------------------------------
class DNAAppError(Exception):
    status_code = 400
    error_code = "bad_request"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class MissingSequenceError(DNAAppError):
    status_code = 400
    error_code = "missing_sequence"


class InvalidSequenceError(DNAAppError):
    status_code = 400
    error_code = "invalid_sequence"


class SequenceTooLongError(DNAAppError):
    status_code = 413
    error_code = "sequence_too_long"


class InvalidAnnotationError(DNAAppError):
    status_code = 422
    error_code = "invalid_annotation"


class ReportGenerationError(DNAAppError):
    status_code = 500
    error_code = "report_generation_failed"


class PDFNotAvailableError(DNAAppError):
    status_code = 501
    error_code = "pdf_not_available"





# ---------------------------------------------------------------------------
# Authentication (401 = "who are you?") and authorization (403 = "not allowed")
# ---------------------------------------------------------------------------
class EmailAlreadyRegisteredError(AppError):
    status_code = 409
    code = "email_already_registered"


class InvalidCredentialsError(AppError):
    """Wrong email OR wrong password - deliberately the same error for both."""

    status_code = 401
    code = "invalid_credentials"


class NotAuthenticatedError(AppError):
    """No (usable) Authorization header was sent."""

    status_code = 401
    code = "not_authenticated"
    headers = {"WWW-Authenticate": "Bearer"}


class TokenExpiredError(AppError):
    """Signature was fine but the 'exp' time has passed -> client should log in again."""

    status_code = 401
    code = "token_expired"
    headers = {"WWW-Authenticate": 'Bearer error="invalid_token", error_description="token expired"'}


class TokenInvalidError(AppError):
    """Bad signature, malformed token, wrong algorithm, missing claims, unknown user..."""

    status_code = 401
    code = "invalid_token"
    headers = {"WWW-Authenticate": 'Bearer error="invalid_token"'}


class ForbiddenError(AppError):
    """Logged in, but not allowed to touch this resource."""

    status_code = 403
    code = "forbidden"


class RecordNotFoundError(AppError):
    status_code = 404
    code = "record_not_found"
