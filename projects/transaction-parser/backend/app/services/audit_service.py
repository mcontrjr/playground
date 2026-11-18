"""Audit trail recording: one append-only row per mutation worth
surfacing in the History page.

`record_event` only adds the event to the session — it never commits.
Callers are expected to call it in the same transaction as the mutation
it describes (immediately before their own `db.commit()`), so the audit
row and the mutation it documents are atomic: either both land or
neither does.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_event(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
    payload: dict[str, Any] | None = None,
    affected_count: int | None = None,
) -> AuditEvent:
    """Add an `AuditEvent` row to the session (not committed).

    `event_type` is one of: category.created|category.renamed|
    category.deleted|category.bucket_changed|keyword.added|
    keyword.removed|transaction.recategorized|
    transaction.bulk_recategorized|bucket.created|bucket.renamed|
    bucket.deleted.
    """
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        payload=payload,
        affected_count=affected_count,
    )
    db.add(event)
    return event
