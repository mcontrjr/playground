"""Pydantic v2 schemas for the workspaces API."""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.accounts import AccountRead
from app.schemas.buckets import BucketRead
from app.schemas.budgets import BudgetExpenseRead
from app.schemas.categories import CategoryRead

#: Username-like: lowercase letters, digits, hyphen, underscore. Checked
#: after normalization (strip + lowercase), so "  Mcontr " is accepted
#: and stored as "mcontr".
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,39}$")

SLUG_RULES = (
    "2–40 characters, starting with a letter or digit; lowercase letters, "
    "digits, hyphens and underscores only."
)


def normalize_slug(raw: str) -> str:
    """Strip surrounding whitespace and lowercase. Does not validate."""
    return raw.strip().lower()


class WorkspaceRead(BaseModel):
    """A workspace's public identity."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{"id": 1, "slug": "init", "name": "init"}]
        },
    )

    id: int
    slug: str
    name: str


class WorkspaceCreate(BaseModel):
    """Request body to create a workspace.

    `slug` is the handle typed on the splash screen to get back in and
    must be unique across the install. `name` is the display label and
    defaults to the slug when omitted.
    """

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"slug": "ada", "name": "Ada's budget"}]}
    )

    slug: str = Field(min_length=2, max_length=40, description=SLUG_RULES)
    name: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str) -> str:
        slug = normalize_slug(value)
        if not SLUG_PATTERN.match(slug):
            raise ValueError(f"Invalid workspace name. {SLUG_RULES}")
        return slug


class SlugAvailability(BaseModel):
    """Answer for the create form's live uniqueness check."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"slug": "ada", "available": True, "reason": None},
                {
                    "slug": "init",
                    "available": False,
                    "reason": "That workspace name is already taken.",
                },
            ]
        }
    )

    slug: str
    available: bool
    reason: str | None = Field(
        default=None,
        description="Why the slug is unavailable — taken, or malformed.",
    )


class WorkspaceBootstrap(BaseModel):
    """Everything the frontend needs to render a loaded workspace.

    One round trip instead of six: the splash screen's spinning logo
    stays up for exactly one request, and the client can seed its React
    Query caches before the first page paints.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "workspace": {"id": 1, "slug": "init", "name": "init"},
                    "has_transactions": True,
                    "transaction_count": 1043,
                    "accounts": [],
                    "buckets": [],
                    "categories": [],
                    "budget_expenses": [],
                }
            ]
        }
    )

    workspace: WorkspaceRead
    has_transactions: bool = Field(
        description=(
            "False until the first successful upload. The frontend hides "
            "every data page from the sidebar while this is false."
        )
    )
    transaction_count: int
    accounts: list[AccountRead]
    buckets: list[BucketRead]
    categories: list[CategoryRead]
    budget_expenses: list[BudgetExpenseRead] = Field(
        description=(
            "Budget lines with no month applied, so `actual_amount` is "
            "always 0 here — the Budget page fetches its own month-scoped "
            "summary. A new workspace starts with none."
        )
    )
