import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Custom exception hierarchy ────────────────────────────────────────────────

class ExpenseTrackerException(Exception):
    """Base exception for this application."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ExpenseNotFoundError(ExpenseTrackerException):
    def __init__(self, expense_id: str) -> None:
        super().__init__(f"Expense '{expense_id}' not found.", 404)


class GeminiAPIError(ExpenseTrackerException):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Gemini API error: {detail}", 503)


class GeminiParseError(ExpenseTrackerException):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Failed to parse Gemini response: {detail}", 422)


class PDFParseError(ExpenseTrackerException):
    def __init__(self, detail: str) -> None:
        super().__init__(f"PDF parsing error: {detail}", 422)


class AuthenticationError(ExpenseTrackerException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, 401)


class UserAlreadyExistsError(ExpenseTrackerException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, 409)


# ── FastAPI exception handlers ────────────────────────────────────────────────

async def expense_tracker_exception_handler(
    request: Request, exc: ExpenseTrackerException
) -> JSONResponse:
    logger.error("%s at %s: %s", exc.__class__.__name__, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error": exc.__class__.__name__},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception at %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": "InternalServerError"},
    )
