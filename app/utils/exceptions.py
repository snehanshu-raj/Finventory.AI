"""Custom exception classes for the application."""


class AppException(Exception):
    """Base application exception with HTTP status code."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "APP_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND")


class ValidationException(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR")


class ExtractionException(AppException):
    """OCR / LLM extraction error."""

    def __init__(self, message: str = "Receipt extraction failed"):
        super().__init__(message=message, status_code=502, error_code="EXTRACTION_ERROR")


class DuplicateException(AppException):
    """Duplicate resource conflict."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409, error_code="DUPLICATE_ERROR")
