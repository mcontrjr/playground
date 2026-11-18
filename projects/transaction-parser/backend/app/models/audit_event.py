"""AuditEvent model: an append-only log of mutations worth surfacing in
the History page (category/bucket/keyword/transaction-recategorize
events). Follows the JSONB pattern established in `preference.py`.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuditEvent(Base):
    """One recorded mutation: what happened, to what, and how many rows
    it affected. Written in the same transaction as the mutation it
    describes (the caller commits)."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_created_at", text("created_at DESC")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    """One of: category.created|category.renamed|category.deleted|
    category.bucket_changed|keyword.added|keyword.removed|
    transaction.recategorized|transaction.bulk_recategorized|
    bucket.created|bucket.renamed|bucket.deleted."""

    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    affected_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"AuditEvent(id={self.id!r}, event_type={self.event_type!r})"
