"""Transaction model — the core parsed/categorized row."""
from datetime import date
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category
    from app.models.ingest import IngestBatch
    from app.models.workspace import Workspace


class Transaction(TimestampMixin, Base):
    """A single parsed transaction row, deduplicated and categorized.

    Idempotency: `content_hash` is sha256(institution | account_hint |
    date_iso | signed_amount_str | normalized_description), excluding
    posted_date/filename so overlapping re-exports dedupe correctly.
    Within one file, rows that hash identically get increasing
    `occurrence_index` values (0..n-1) so legitimate duplicate purchases
    both insert, while re-uploading the same file reproduces the same
    indices and therefore dedupes against the existing rows.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        # `workspace_id` is part of the idempotency key, not just a filter:
        # content_hash is derived purely from the statement's own contents,
        # so two workspaces uploading the same file produce identical
        # hashes. Without the workspace in this constraint, the second
        # workspace's rows would be silently discarded as already-ingested
        # duplicates of the first's.
        UniqueConstraint(
            "workspace_id",
            "content_hash",
            "occurrence_index",
            name="uq_transactions_hash_occurrence",
        ),
        CheckConstraint(
            "category_source IN ('keyword', 'manual', 'transfer', 'default')",
            name="ck_transactions_category_source",
        ),
        CheckConstraint(
            "recurrence IS NULL OR recurrence IN ('monthly', 'yearly')",
            name="ck_transactions_recurrence",
        ),
        Index("ix_transactions_txn_date", "txn_date"),
        Index("ix_transactions_category_id", "category_id"),
        Index("ix_transactions_account_id", "account_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("ingest_batches.id", ondelete="CASCADE"), nullable=False
    )
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_description: Mapped[str] = mapped_column(String(512), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bank_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category_source: Mapped[str] = mapped_column(String(16), nullable=False)
    matched_keyword: Mapped[str | None] = mapped_column(String(128), nullable=True)
    """The keyword that won when category_source is 'keyword'/'transfer';
    null for 'default' (nothing matched) and for 'manual'/'bulk' (a person
    chose). Recorded at decision time so a row stays explainable even after
    the keyword is renamed, reprioritized, or deleted."""
    content_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    occurrence_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_row: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    recurrence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    """One of 'monthly' / 'yearly' when is_recurring is set; null otherwise.
    Drives the site-wide "recurring" badge/filter so a subscription or an
    annual payment can be flagged independent of its category."""

    workspace: Mapped["Workspace"] = relationship()
    account: Mapped["Account"] = relationship(back_populates="transactions")
    batch: Mapped["IngestBatch"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"Transaction(id={self.id!r}, date={self.txn_date!r}, "
            f"amount={self.amount!r}, hash={self.content_hash[:8]!r})"
        )
