"""Shared response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """Stable API error envelope."""

    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    retryable: bool = False
    request_id: str | None = Field(default=None, alias="requestId")

    model_config = {"populate_by_name": True}
