"""Parse-failure review endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_workspace
from app.models import ParseFailure, Workspace
from app.schemas.failures import ParseFailurePatch, ParseFailureRead

router = APIRouter(prefix="/failures", tags=["failures"])


@router.get(
    "",
    response_model=list[ParseFailureRead],
    summary="List parse failures",
    description="Rows that failed to parse during ingest. Filter by resolution state.",
)
def list_failures(
    resolved: bool | None = None,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> list[ParseFailureRead]:
    stmt = (
        select(ParseFailure)
        .where(ParseFailure.workspace_id == ws.id)
        .order_by(ParseFailure.created_at.desc())
    )
    if resolved is not None:
        stmt = stmt.where(ParseFailure.resolved == resolved)
    failures = db.execute(stmt).scalars().all()
    return [ParseFailureRead.model_validate(f) for f in failures]


@router.patch(
    "/{failure_id}",
    response_model=ParseFailureRead,
    summary="Mark a parse failure resolved/unresolved",
)
def patch_failure(
    failure_id: int,
    payload: ParseFailurePatch,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> ParseFailureRead:
    failure = db.get(ParseFailure, failure_id)
    if failure is None or failure.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failure not found")

    failure.resolved = payload.resolved
    db.commit()
    db.refresh(failure)
    return ParseFailureRead.model_validate(failure)
