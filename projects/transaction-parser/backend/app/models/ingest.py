"""IngestBatch and ParseFailure models."""
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.institution import Institution
    from app.models.transaction import Transaction


class IngestBatch(TimestampMixin, Base):
    """One upload/ingest run of a single CSV file."""

    __tablename__ = "ingest_batches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'completed_with_errors', 'failed')",
            name="ck_ingest_batches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )

    institution: Mapped["Institution"] = relationship()
    account: Mapped["Account | None"] = relationship(back_populates="ingest_batches")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    failures: Mapped[list["ParseFailure"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"IngestBatch(id={self.id!r}, filename={self.filename!r}, status={self.status!r})"


class ParseFailure(TimestampMixin, Base):
    """A single row that failed to parse during an ingest batch."""

    __tablename__ = "parse_failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("ingest_batches.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    batch: Mapped["IngestBatch"] = relationship(back_populates="failures")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ParseFailure(id={self.id!r}, batch_id={self.batch_id!r}, line={self.line_number!r})"
