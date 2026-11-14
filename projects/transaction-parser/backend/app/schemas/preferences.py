"""Pydantic v2 schemas for the user-preferences cache endpoint."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PreferenceRead(BaseModel):
    """A single persisted preference value."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"key": "theme", "value": {"theme": "gruvbox"}}]
        }
    )

    key: str
    value: dict[str, Any]


class PreferenceWrite(BaseModel):
    """Request body to set one preference. ``value`` is stored verbatim
    and returned verbatim on the next GET — the backend never interprets
    it, it's purely a cache for whatever the frontend wants persisted
    (active theme, a page's last-used filter selections, etc.)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"value": {"accountIds": [1, 2], "monthKeys": ["2026-10"]}}]}
    )

    value: dict[str, Any] = Field(description="Opaque JSON blob to persist under this key.")
