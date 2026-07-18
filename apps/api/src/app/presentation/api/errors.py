"""Global exception handlers → stable problem details."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infrastructure.logging.setup import get_logger
from app.shared.exceptions import AppError

logger = get_logger("app.api")


def _request_id(request: Request) -> str | None:
    ctx = getattr(request.state, "request_context", None)
    return getattr(ctx, "request_id", None) if ctx else request.headers.get("X-Request-Id")


def _problem(
    *,
    code: str,
    message: str,
    status: int,
    request: Request,
    details: list[dict[str, Any]] | None = None,
    retryable: bool = False,
) -> JSONResponse:
    body = {
        "code": code,
        "message": message,
        "details": details or [],
        "retryable": retryable,
        "requestId": _request_id(request),
    }
    return JSONResponse(status_code=status, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log = logger.warning if exc.http_status < 500 else logger.error
        log(
            "app_error",
            code=exc.code,
            message=exc.message,
            status=exc.http_status,
            retryable=exc.retryable,
        )
        return _problem(
            code=exc.code,
            message=exc.message,
            status=exc.http_status,
            request=request,
            details=exc.details,
            retryable=exc.retryable,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", ()))
            details.append({"field": loc, "issue": err.get("msg", "invalid")})
        return _problem(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            status=422,
            request=request,
            details=details,
            retryable=False,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(
            code="HTTP_ERROR",
            message=str(exc.detail),
            status=exc.status_code,
            request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return _problem(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status=500,
            request=request,
            retryable=True,
        )
