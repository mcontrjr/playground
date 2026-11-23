"""Pydantic v2 schemas for category CRUD, keyword management, and the
keyword impact-preview dry-run."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ImpactAction = Literal["add_keyword", "remove_keyword"]


class CategoryKeywordRead(BaseModel):
    """A single keyword rule belonging to a category."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"id": 14, "keyword": "STARBUCKS"}]},
    )

    id: int
    keyword: str


class CategoryRead(BaseModel):
    """A transaction category, including its keywords and transaction count."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 8,
                    "name": "Food",
                    "is_system": False,
                    "excluded_from_analytics": False,
                    "priority": 7,
                    "bucket_id": 2,
                    "group": "LIFESTYLE",
                    "keywords": [{"id": 14, "keyword": "STARBUCKS"}, {"id": 15, "keyword": "CHIPOTLE"}],
                    "transaction_count": 63,
                }
            ]
        },
    )

    id: int
    name: str
    is_system: bool
    excluded_from_analytics: bool
    priority: int
    bucket_id: int
    group: str = Field(
        description="The bucket's name, raw uppercase (e.g. ESSENTIALS, LIFESTYLE, INCOME, TRANSFERS, SAVINGS, OTHER). Serialized from bucket_id for frontend compat.",
    )
    keywords: list[CategoryKeywordRead]
    transaction_count: int


class CategoryCreate(BaseModel):
    """Request body to create a new (non-system) category."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Subscriptions", "priority": 20, "excluded_from_analytics": False, "bucket_id": 2}]}
    )

    name: str = Field(min_length=1, max_length=128)
    priority: int | None = Field(
        default=None,
        description="Lower matches first. Defaults to one past the current max priority.",
    )
    excluded_from_analytics: bool = False
    bucket_id: int | None = Field(
        default=None,
        description="Bucket this category belongs to. Defaults to the OTHER bucket when omitted.",
    )


class CategoryPatch(BaseModel):
    """Request body to rename a category and/or edit its priority or
    analytics-exclusion flag. All fields optional; only provided fields
    are changed."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Dining & Coffee"}]})

    name: str | None = Field(default=None, min_length=1, max_length=128)
    priority: int | None = None
    excluded_from_analytics: bool | None = None
    bucket_id: int | None = None


class CategoryPatchResponse(BaseModel):
    """A patched category plus how many transactions were affected by
    the rename (informational only — renaming does not move rows, it
    just changes what their existing category_id displays as)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": {
                        "id": 8,
                        "name": "Dining & Coffee",
                        "is_system": False,
                        "excluded_from_analytics": False,
                        "priority": 7,
                        "keywords": [{"id": 14, "keyword": "STARBUCKS"}],
                        "transaction_count": 63,
                    },
                    "affected_transaction_count": 63,
                }
            ]
        }
    )

    category: CategoryRead
    affected_transaction_count: int = Field(
        description="Number of transactions currently assigned to this category."
    )


class CategoryDeleteResponse(BaseModel):
    """Result of deleting a non-system category: its transactions are
    reassigned to Uncategorized and its keywords cascade-deleted."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"deleted_category_id": 19, "reassigned_transaction_count": 4}]
        }
    )

    deleted_category_id: int
    reassigned_transaction_count: int = Field(
        description="Transactions moved off the deleted category."
    )
    rematched_transaction_count: int = Field(
        default=0,
        description=(
            "Of those, how many the remaining rules claimed for a real "
            "category rather than leaving in Uncategorized. 0 when "
            "rematch was not requested."
        ),
    )


class CategoryKeywordCreate(BaseModel):
    """Request body to add a new keyword to a category."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"keyword": "peet's coffee", "apply_to_existing": True}]}
    )

    keyword: str = Field(min_length=1, max_length=128)
    apply_to_existing: bool = Field(
        default=False,
        description=(
            "If true, re-run the categorizer with this keyword added and "
            "apply the result to every non-manual transaction that would "
            "now match it (manual recategorizations are never touched)."
        ),
    )


class CategoryKeywordCreateResponse(BaseModel):
    """Result of adding a keyword, including how many rows were updated
    if apply_to_existing was set."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"keyword": {"id": 14, "keyword": "PEET'S COFFEE"}, "applied_count": 6}]
        }
    )

    keyword: CategoryKeywordRead
    applied_count: int = Field(
        description="Transactions updated to this category as a result of apply_to_existing. 0 if not requested."
    )


class CategoryKeywordDeleteResponse(BaseModel):
    """Result of deleting a keyword, including how many rows were
    re-categorized if ``reapply=true`` was passed."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"deleted_keyword_id": 14, "reapplied_count": 6}]}
    )

    deleted_keyword_id: int
    reapplied_count: int = Field(
        description="Transactions re-categorized (to whatever now wins) as a result of reapply=true. 0 otherwise."
    )


class ImpactPreviewRequest(BaseModel):
    """Request body for a keyword-change dry-run."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "add_keyword", "category_id": 8, "keyword": "peet's coffee"}
            ]
        }
    )

    action: ImpactAction
    category_id: int = Field(description="Category the keyword would be added to or removed from.")
    keyword: str = Field(min_length=1, max_length=128)


class ImpactPreviewTransaction(BaseModel):
    """One sample row in an impact preview, showing the move it would make."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 212,
                    "description": "PEET'S COFFEE #412 SAN JOSE CA",
                    "current_category_id": 25,
                    "current_category_name": "Uncategorized",
                    "new_category_id": 8,
                    "new_category_name": "Food",
                }
            ]
        }
    )

    id: int
    description: str
    current_category_id: int | None
    current_category_name: str | None
    new_category_id: int | None
    new_category_name: str | None


class ImpactPreviewBreakdownEntry(BaseModel):
    """Count of transactions moving between one from/to category pair."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"from_category_id": 25, "from_category": "Uncategorized", "to_category_id": 8, "to_category": "Food", "count": 6}]
        }
    )

    from_category_id: int | None
    from_category: str | None
    to_category_id: int | None
    to_category: str | None
    count: int


class ImpactPreviewResponse(BaseModel):
    """Dry-run result for a keyword add/remove, before applying it."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "affected_count": 6,
                    "sample": [
                        {
                            "id": 212,
                            "description": "PEET'S COFFEE #412 SAN JOSE CA",
                            "current_category_id": 25,
                            "current_category_name": "Uncategorized",
                            "new_category_id": 8,
                            "new_category_name": "Food",
                        }
                    ],
                    "breakdown": [
                        {"from_category_id": 25, "from_category": "Uncategorized", "to_category_id": 8, "to_category": "Food", "count": 6}
                    ],
                }
            ]
        }
    )

    affected_count: int
    sample: list[ImpactPreviewTransaction] = Field(max_length=20)
    breakdown: list[ImpactPreviewBreakdownEntry]


class ErrorDetail(BaseModel):
    """Generic structured error body used across the categories API."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": "SYSTEM_CATEGORY_UNDELETABLE", "message": "System categories cannot be deleted."}
            ]
        }
    )

    code: str
    message: str
    owning_category_id: int | None = None
    owning_category_name: str | None = None


# --- Clash reconciliation ---------------------------------------------------
# A "clash" is a description claimed by more than one category. The
# categorizer always resolves it silently (transfer-first, then priority),
# so these schemas exist to surface that decision and let the user override.


class ClashClaim(BaseModel):
    """One category's competing claim on a transaction's description."""

    category_id: int
    category_name: str
    keyword: str = Field(description="The matching keyword behind this claim.")
    priority: int
    stage: str = Field(description="'transfer' (decided pre-priority) or 'keyword'.")
    is_winner: bool = Field(description="True for the claim the categorizer currently honors.")


class TransactionClashRead(BaseModel):
    """A transaction claimed by two or more categories."""

    transaction_id: int
    description: str
    txn_date: date
    amount: Decimal
    current_category_id: int | None
    current_category_name: str | None
    category_source: str
    is_settled: bool = Field(
        description="True when manual/bulk — the user already decided; not actionable."
    )
    transfer_decided: bool = Field(
        description=(
            "True when the winner won at the transfer stage, which runs before "
            "priority is consulted — so no reorder can change this one."
        )
    )
    claims: list[ClashClaim]


class ClashListResponse(BaseModel):
    """Outstanding clashes: rows where priority silently chose for the user."""

    total: int = Field(description="Clashing rows matching the requested scope.")
    settled_count: int = Field(description="Clashing rows already settled manually/bulk.")
    dismissed_count: int = Field(
        default=0,
        description=(
            "Clashing rows hidden because the user judged the pairing "
            "correct. Surfaced so a suppressed queue never looks empty."
        ),
    )
    items: list[TransactionClashRead]


class ClashResolveRequest(BaseModel):
    """Settle a clash by explicit user choice, written as
    category_source='manual' so it stays sticky forever.

    scope='row' pins only the listed transactions. scope='all_matching'
    also pins every other unsettled row sharing `keyword`, so a recurring
    merchant needn't be resolved one row at a time.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"transaction_ids": [101], "category_id": 30, "scope": "row"}]
        }
    )

    transaction_ids: list[int] = Field(min_length=1)
    category_id: int = Field(description="The category the user chose.")
    scope: Literal["row", "all_matching"] = "row"
    keyword: str | None = Field(
        default=None,
        description="Required when scope='all_matching': the keyword to match siblings on.",
    )


class ClashResolveResponse(BaseModel):
    resolved_count: int = Field(description="Rows pinned to the chosen category (manual).")
    category_id: int
    category_name: str


class ReprioritizeRequest(BaseModel):
    """Re-prioritize categories; lower numbers match first.

    Defaults to a dry run, because priority is global: a reorder meant to
    fix one merchant can move unrelated rows sharing a keyword.
    """

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"priorities": {"30": 2}, "dry_run": True}]}
    )

    priorities: dict[int, int] = Field(
        description="category_id -> new priority. Only listed categories change."
    )
    dry_run: bool = Field(default=True, description="When true, report without writing.")


class ReprioritizeMove(BaseModel):
    transaction_id: int
    description: str
    from_category_name: str | None
    to_category_name: str | None


class ReprioritizeResponse(BaseModel):
    dry_run: bool
    candidate_count: int = Field(description="Rows whose category would change.")
    affected_count: int = Field(description="Rows actually updated; 0 on a dry run.")
    moves: list[ReprioritizeMove]


class ClashDismissRequest(BaseModel):
    """Mark a conflict as reviewed-and-fine so it stops being listed.

    Scope is decided by `transaction_id`: omit it to dismiss the whole
    winner-vs-loser pairing (covers future rows too, including ones a
    re-import creates); pass it to dismiss just that one record.

    This never changes the transaction's category. It records a judgment
    about the rules, unlike resolving — which pins the row as 'manual'.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"winner_category_id": 1, "loser_category_id": 10}]
        }
    )

    winner_category_id: int = Field(description="The category that currently wins.")
    loser_category_id: int = Field(description="The competing category being overruled.")
    transaction_id: int | None = Field(
        default=None,
        description="Omit for a rule-level dismissal; set to scope it to one record.",
    )
    note: str | None = Field(default=None, max_length=256)


class ClashDismissalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    winner_category_id: int
    winner_category_name: str
    loser_category_id: int
    loser_category_name: str
    transaction_id: int | None
    note: str | None
    hidden_count: int = Field(
        description="Clashing records this dismissal currently hides."
    )


class ClashDismissalListResponse(BaseModel):
    total: int = Field(description="Dismissal rules on record.")
    hidden_total: int = Field(
        description="Clashing records hidden across all dismissals."
    )
    items: list[ClashDismissalRead]
