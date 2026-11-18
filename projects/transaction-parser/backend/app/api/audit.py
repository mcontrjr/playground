"""Read-only audit trail endpoint backing the History page."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent
from app.schemas.audit import AuditEventRead, AuditPage

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "",
    response_model=AuditPage,
    summary="List audit events",
    description="Paginated audit trail, newest first (created_at desc, id desc).",
)
def list_audit_events(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> AuditPage:
    total = db.execute(select(func.count()).select_from(AuditEvent)).scalar_one()

    rows = (
        db.execute(
            select(AuditEvent)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return AuditPage(
        items=[AuditEventRead.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
