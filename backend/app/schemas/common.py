from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.utcnow())
