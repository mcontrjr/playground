"""Pydantic v2 schemas for the audit trail / History page."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRead(BaseModel):
    """A single recorded mutation."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 42,
                    "event_type": "category.renamed",
                    "entity_type": "category",
                    "entity_id": 8,
                    "description": "Renamed category 'Food' to 'Dining & Coffee'.",
                    "payload": {"from": "Food", "to": "Dining & Coffee"},
                    "affected_count": 63,
                    "created_at": "2026-11-14T12:00:00Z",
                }
            ]
        },
    )

    id: int
    event_type: str
    entity_type: str
    entity_id: int | None
    description: str
    payload: dict[str, Any] | None
    affected_count: int | None
    created_at: datetime


class AuditPage(BaseModel):
    """A page of audit events, newest first."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"items": [], "total": 0, "limit": 50, "offset": 0}]
        }
    )

    items: list[AuditEventRead]
    total: int
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
