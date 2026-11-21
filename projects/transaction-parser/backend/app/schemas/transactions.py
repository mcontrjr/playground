"""Pydantic v2 schemas for the transactions query/recategorize API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionSortField = Literal["txn_date", "amount", "description", "category"]
SortOrder = Literal["asc", "desc"]


class TransactionRead(BaseModel):
    """A single parsed, categorized transaction."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 101,
                    "account_id": 3,
                    "account_name": "Amex ···21003",
                    "institution_code": "amex",
                    "batch_id": 7,
                    "txn_date": "2026-10-04",
                    "posted_date": "2026-10-05",
                    "description": "STARBUCKS STORE 01234 SAN FRANCISCO CA",
                    "amount": "-6.75",
                    "bank_category": "Restaurant-Fast Food",
                    "category_id": 8,
                    "category_name": "Food",
                    "category_source": "keyword",
                    "raw_row": {"Description": "STARBUCKS STORE 01234 SAN FRANCISCO CA", "Amount": "-6.75"},
                    "created_at": "2026-11-13T18:05:00Z",
                }
            ]
        },
    )

    id: int
    account_id: int
    account_name: str = Field(description="Account display name, joined for convenience.")
    institution_code: str = Field(description="The source bank/card, e.g. 'schwab', 'amex' — keys which raw_row columns to expect.")
    batch_id: int
    txn_date: date
    posted_date: date | None
    description: str
    amount: Decimal = Field(description="Signed amount; negative = money out, positive = money in.")
    bank_category: str | None
    category_id: int | None
    category_name: str | None = Field(description="Joined category name, null if uncategorized.")
    category_source: str = Field(description="One of: keyword, manual, transfer, default.")
    is_recurring: bool = Field(description="Whether this transaction is flagged as a recurring bill/subscription.")
    recurrence: Literal["monthly", "yearly"] | None = Field(
        default=None, description="Recurrence cadence when is_recurring is true."
    )
    raw_row: dict[str, str] = Field(
        description=(
            "The original CSV row, keyed by that bank's own column names — "
            "shape differs per institution_code, never padded with nulls "
            "for columns a different bank happens to have."
        )
    )
    created_at: datetime


class MonthOption(BaseModel):
    """One calendar month that has at least one transaction, computed in
    SQL so the frontend never has to derive "months with data" from the
    full date range (which wrongly includes empty months)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [{"key": "2026-10", "label": "Oct 2026", "from": "2026-10-01", "to": "2026-10-31"}]
        },
    )

    key: str = Field(description="YYYY-MM")
    label: str = Field(description="Human label, e.g. 'Oct 2026'.")
    from_: date = Field(alias="from", description="First day of the month.")
    to: date = Field(description="Last day of the month.")


class TransactionFacets(BaseModel):
    """Which account/category/month filter options currently have at
    least one matching transaction, each computed against every *other*
    active filter (not its own dimension) — see GET /transactions/facets.
    Drives dimming unavailable chips in the Records filter bar."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"account_ids": [1, 3], "category_ids": [5, 8, 12], "month_keys": ["2026-10", "2026-11"]}]
        }
    )

    account_ids: list[int] = Field(description="Account ids with at least one matching transaction.")
    category_ids: list[int] = Field(description="Category ids with at least one matching transaction.")
    month_keys: list[str] = Field(description="'YYYY-MM' months with at least one matching transaction.")


class TransactionListResponse(BaseModel):
    """Paginated envelope for transaction listing."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": 101,
                            "account_id": 3,
                            "account_name": "Amex ···21003",
                            "batch_id": 7,
                            "txn_date": "2026-10-04",
                            "posted_date": "2026-10-05",
                            "description": "STARBUCKS STORE 01234 SAN FRANCISCO CA",
                            "amount": "-6.75",
                            "bank_category": "Restaurant-Fast Food",
                            "category_id": 8,
                            "category_name": "Food",
                            "category_source": "keyword",
                            "created_at": "2026-11-13T18:05:00Z",
                        }
                    ],
                    "total": 448,
                    "limit": 50,
                    "offset": 0,
                }
            ]
        }
    )

    items: list[TransactionRead]
    total: int = Field(description="Total matching rows across all pages, before limit/offset.")
    limit: int
    offset: int


class TransactionPatch(BaseModel):
    """Request body to manually recategorize and/or flag the recurrence
    of a single transaction.

    Setting `category_id` also sets `category_source='manual'`, which
    makes the row sticky: it will no longer be moved by keyword
    add/remove `apply_to_existing` operations. `is_recurring`/`recurrence`
    are independent of categorization and may be set on their own.
    """

    model_config = ConfigDict(json_schema_extra={"examples": [{"category_id": 12}]})

    category_id: int | None = Field(default=None, description="The category to assign.")
    is_recurring: bool | None = Field(
        default=None, description="Flag/unflag this transaction as a recurring bill/subscription."
    )
    recurrence: Literal["monthly", "yearly"] | None = Field(
        default=None, description="Cadence to set when flagging is_recurring=true."
    )


class BulkRecategorizeRequest(BaseModel):
    """Request body to recategorize many transactions at once, recorded
    as a single audit event rather than one per row. Sets
    category_source='bulk' — sticky against keyword apply_to_existing
    operations, same as 'manual', but distinguishable as having come
    from a bulk action rather than a one-by-one edit."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"transaction_ids": [101, 102, 103], "category_id": 12}]}
    )

    transaction_ids: list[int] = Field(min_length=1, description="Ids of the transactions to recategorize.")
    category_id: int = Field(description="The category to assign to all given transactions.")


class BulkRecategorizeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"affected_count": 3, "category_id": 12, "category_name": "Groceries"}]}
    )

    affected_count: int = Field(description="Number of transactions updated.")
    category_id: int
    category_name: str


class RecategorizeAllRequest(BaseModel):
    """Request body to re-run the current categorization rules over all
    existing transactions. Defaults to a dry run so the blast radius is
    always inspectable before anything is written."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"dry_run": True}]})

    dry_run: bool = Field(
        default=True,
        description=(
            "When true (the default), report what would change without "
            "writing anything. Set false to actually apply the moves."
        ),
    )


class RecategorizeAllMove(BaseModel):
    """One transaction whose stored category disagrees with the rules."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transaction_id": 101,
                    "description": "CAPITAL ONE MOBILE PMT",
                    "from_category_id": 26,
                    "from_category_name": "Uncategorized",
                    "to_category_id": 20,
                    "to_category_name": "Payments & Transfers",
                    "to_source": "transfer",
                }
            ]
        }
    )

    transaction_id: int
    description: str
    from_category_id: int | None
    from_category_name: str | None
    to_category_id: int | None
    to_category_name: str | None
    to_source: str = Field(description="One of: keyword, transfer, default.")


class RecategorizeAllResponse(BaseModel):
    """Outcome of a recategorize-all pass. ``affected_count`` is 0 on a
    dry run; ``moves`` lists the changes either way."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"dry_run": True, "candidate_count": 4, "affected_count": 0, "moves": []}]
        }
    )

    dry_run: bool
    candidate_count: int = Field(description="Transactions whose category would change.")
    affected_count: int = Field(description="Transactions actually updated; 0 on a dry run.")
    skipped_sticky_count: int = Field(
        description="Manual/bulk rows excluded from consideration entirely."
    )
    moves: list[RecategorizeAllMove] = Field(
        default_factory=list, description="The per-transaction changes, capped for readability."
    )
