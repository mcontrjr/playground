"""Pydantic v2 schemas for the accounts API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AccountRead(BaseModel):
    """An account discovered during ingest, with institution info and a
    transaction count for convenience in the frontend account picker."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "institution_code": "amex",
                    "institution_name": "American Express",
                    "account_hint": "21003",
                    "display_name": "Amex ···21003",
                    "kind": "card",
                    "transaction_count": 105,
                }
            ]
        },
    )

    id: int
    institution_code: str
    institution_name: str
    account_hint: str
    display_name: str
    kind: str = Field(description="One of: card, checking.")
    transaction_count: int


class AccountPatch(BaseModel):
    """Request body to rename an account's display name."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"display_name": "Amex Gold (Martin)"}]}
    )

    display_name: str = Field(min_length=1, max_length=128)
