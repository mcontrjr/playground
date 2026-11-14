"""Pydantic v2 schemas for the upload/ingest-batch API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.failures import ParseFailureRead


class BatchCounts(BaseModel):
    """Row-count breakdown for one ingest batch."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"total": 105, "inserted": 105, "duplicates": 0, "failures": 0}]
        }
    )

    total: int = Field(description="Total data rows seen in the file (parsed + failed).")
    inserted: int = Field(description="Rows newly inserted (not already present by content hash).")
    duplicates: int = Field(description="Rows that matched an already-inserted row and were skipped.")
    failures: int = Field(description="Rows that failed to parse and were isolated as ParseFailures.")


class BatchSummary(BaseModel):
    """Summary of one ingest batch, returned from the upload endpoint
    and from the batch list/detail endpoints."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 7,
                    "filename": "amex_90_day.csv",
                    "institution": "amex",
                    "status": "completed",
                    "counts": {"total": 105, "inserted": 105, "duplicates": 0, "failures": 0},
                    "created_at": "2026-11-13T18:05:00Z",
                }
            ]
        },
    )

    id: int
    filename: str
    institution: str = Field(description="Institution code, e.g. 'amex', 'capital_one'.")
    status: str = Field(description="One of: completed, completed_with_errors, failed.")
    counts: BatchCounts
    created_at: datetime


class BatchDetail(BatchSummary):
    """Batch summary plus the inline list of parse failures, if any."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 7,
                    "filename": "schwab_malformed.csv",
                    "institution": "schwab",
                    "status": "completed_with_errors",
                    "counts": {"total": 67, "inserted": 66, "duplicates": 0, "failures": 1},
                    "created_at": "2026-11-13T18:05:00Z",
                    "failures": [
                        {
                            "id": 3,
                            "batch_id": 7,
                            "line_number": 12,
                            "raw_line": '"11/09/2026","Posted","ACH","","BAD ROW NO AMOUNT","","","$899.19"',
                            "error_type": "ValueError",
                            "error_message": "row has neither Withdrawal nor Deposit value",
                            "resolved": False,
                            "created_at": "2026-11-13T18:05:00Z",
                        }
                    ],
                }
            ]
        },
    )

    failures: list[ParseFailureRead] = Field(default_factory=list)


class AmbiguousInstitutionResponse(BaseModel):
    """409 response body when header-based detection can't disambiguate
    the institution (today: Capital One vs. Discover share a header)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "AMBIGUOUS_INSTITUTION",
                    "candidates": ["capital_one", "discover"],
                    "message": (
                        "Could not determine the institution from the file's "
                        "header or filename. Retry the upload with an explicit "
                        "'institution' field set to one of the candidates."
                    ),
                }
            ]
        }
    )

    code: str = "AMBIGUOUS_INSTITUTION"
    candidates: list[str]
    message: str
