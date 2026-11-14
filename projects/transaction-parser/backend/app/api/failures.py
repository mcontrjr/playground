"""Parse-failure review endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ParseFailure
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
) -> list[ParseFailureRead]:
    stmt = select(ParseFailure).order_by(ParseFailure.created_at.desc())
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
) -> ParseFailureRead:
    failure = db.get(ParseFailure, failure_id)
    if failure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failure not found")

    failure.resolved = payload.resolved
    db.commit()
    db.refresh(failure)
    return ParseFailureRead.model_validate(failure)
