"""Account model: a specific card/checking account under an institution."""
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ingest import IngestBatch
    from app.models.institution import Institution
    from app.models.transaction import Transaction
    from app.models.workspace import Workspace


class Account(TimestampMixin, Base):
    """A specific account (card or checking) discovered during ingest.

    Accounts are created lazily the first time a matching row is parsed;
    `account_hint` is the distinguishing fragment found in the source file
    (e.g. Amex last-5, a card number fragment, or the literal "checking").
    """

    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "institution_id",
            "account_hint",
            name="uq_accounts_institution_hint",
        ),
        CheckConstraint("kind IN ('card', 'checking')", name="ck_accounts_kind"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    account_hint: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="accounts")
    institution: Mapped["Institution"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    ingest_batches: Mapped[list["IngestBatch"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Account(id={self.id!r}, hint={self.account_hint!r}, kind={self.kind!r})"
