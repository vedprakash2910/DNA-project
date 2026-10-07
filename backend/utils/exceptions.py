
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
