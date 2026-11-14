"""Pydantic v2 schemas for parse failures."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParseFailureRead(BaseModel):
    """A single row that failed to parse during an ingest batch."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "batch_id": 7,
                    "line_number": 42,
                    "raw_line": "11/07/2026,BAD ROW NO AMOUNT,MARTIN CONTRERAS,-21003,",
                    "error_type": "ValueError",
                    "error_message": "could not parse money value: ''",
                    "resolved": False,
                    "created_at": "2026-11-13T18:05:00Z",
                }
            ]
        },
    )

    id: int
    batch_id: int
    line_number: int = Field(description="1-indexed line number within the source CSV; line 1 is the header.")
    raw_line: str = Field(description="The raw, comma-joined CSV fields for the failed row.")
    error_type: str = Field(description="Python exception class name raised while parsing this row.")
    error_message: str
    resolved: bool
    created_at: datetime


class ParseFailurePatch(BaseModel):
    """Request body for marking a parse failure resolved/unresolved."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"resolved": True}]}
    )

    resolved: bool = Field(description="Set true once the failure has been reviewed/handled.")
