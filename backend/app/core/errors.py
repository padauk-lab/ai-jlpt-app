"""One error format for the whole API, as the contract says:

{"error": {"code": "validation_error", "message": "...", "fields": {"last_score": "..."}}}

"fields" appears only for validation errors. The app shows a Burmese message based on "code".
Unexpected errors return a generic 500 and never leak internal details to the app.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Default code for each HTTP status, used when an error has no specific code.
DEFAULT_CODES = {
    400: "bad_request",
    401: "not_logged_in",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    500: "server_error",
    503: "service_unavailable",
}


class ApiError(Exception):
    """Raise this in endpoints to send a contract-style error.

    Example: raise ApiError(409, "email_taken", "This email is already registered.")
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        self.headers = headers  # extra response headers, for example Retry-After on 429


def error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return {"error": error}


async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.fields), headers=exc.headers
    )


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = DEFAULT_CODES.get(exc.status_code, "error")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(status_code=exc.status_code, content=error_body(code, message), headers=exc.headers)


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for err in exc.errors():
        # loc looks like ("body", "last_score"); skip the first part ("body", "query", "path").
        name = ".".join(str(part) for part in err.get("loc", ())[1:]) or "request"
        fields.setdefault(name, err.get("msg", "Invalid value."))
    return JSONResponse(status_code=422, content=error_body("validation_error", "Invalid input.", fields))


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Full details go to the server log only, never to the app.
    logger.exception("Unexpected error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=error_body("server_error", "Something went wrong. Please try again."))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unexpected_error)
