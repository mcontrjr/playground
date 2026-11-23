"""Clash dismissal: a conflict the user reviewed and judged fine as-is."""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    pass


class ClashDismissal(TimestampMixin, Base):
    """A clash the user has reviewed and chosen to stop being shown.

    Two shapes, distinguished by which columns are set:

    - **Rule-level** (``transaction_id`` null): "when these two
      categories compete and this one wins, that's correct". Keyed by
      the winning + losing category pair, so it suppresses every current
      *and future* row of that shape — including rows created by a
      re-import, which a per-row dismissal would miss.
    - **Row-level** (``transaction_id`` set): this one specific record
      is fine, without judging the pairing generally.

    Deliberately NOT the same as resolving a clash. Resolving writes
    ``category_source='manual'``, which pins the row and opts it out of
    future rule changes. A dismissal records a *judgment about the
    rules* and leaves the transaction's categorization untouched, so a
    later keyword fix still flows through to it.

    Rows cascade on category delete: a pairing involving a category that
    no longer exists can't recur, so the dismissal is meaningless.
    """

    __tablename__ = "clash_dismissals"
    __table_args__ = (
        # Uniqueness is enforced by two *partial* unique indexes created in
        # the migration, not a table constraint: Postgres treats NULLs as
        # distinct, so a plain UniqueConstraint over a nullable
        # transaction_id would happily allow duplicate rule-level rows.
        Index(
            "uq_clash_dismissal_rule",
            "winner_category_id",
            "loser_category_id",
            unique=True,
            postgresql_where=text("transaction_id IS NULL"),
        ),
        Index(
            "uq_clash_dismissal_row",
            "winner_category_id",
            "loser_category_id",
            "transaction_id",
            unique=True,
            postgresql_where=text("transaction_id IS NOT NULL"),
        ),
        Index("ix_clash_dismissals_transaction_id", "transaction_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    winner_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    loser_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True
    )
    """Null for a rule-level dismissal; set for a single-record one."""

    note: Mapped[str | None] = mapped_column(String(256), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        scope = f"txn={self.transaction_id}" if self.transaction_id else "rule"
        return (
            f"ClashDismissal(id={self.id!r}, {scope}, "
            f"winner={self.winner_category_id!r}, loser={self.loser_category_id!r})"
        )
