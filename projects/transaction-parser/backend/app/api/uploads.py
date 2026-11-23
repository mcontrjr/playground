"""Upload / ingest-batch endpoints.

``POST /uploads`` accepts one CSV file per request (multipart) plus an
optional ``institution`` form field that, when provided, always wins
over header/filename auto-detection — this is also the retry path a
client takes after receiving a 409 ambiguity response.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_workspace
from app.models import IngestBatch, Workspace
from app.parsers.registry import UnknownFormatError
from app.schemas.uploads import BatchCounts, BatchDetail, BatchSummary
from app.services.ingest_service import (
    AmbiguousInstitutionError,
    InvalidFileExtensionError,
    UnknownInstitutionCodeError,
    ingest_file,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _batch_to_summary(batch: IngestBatch) -> BatchSummary:
    return BatchSummary(
        id=batch.id,
        filename=batch.filename,
        institution=batch.institution.code,
        status=batch.status,
        counts=BatchCounts(
            total=batch.row_count,
            inserted=batch.inserted_count,
            duplicates=batch.duplicate_count,
            failures=batch.failure_count,
        ),
        created_at=batch.created_at,
    )


def _batch_to_detail(batch: IngestBatch) -> BatchDetail:
    summary = _batch_to_summary(batch)
    return BatchDetail(
        **summary.model_dump(),
        failures=list(batch.failures),
    )


@router.post(
    "",
    response_model=BatchDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a bank/card CSV statement",
    description=(
        "Accepts a single CSV file (multipart/form-data) and ingests it: "
        "detects the institution, parses rows, deduplicates by content "
        "hash, categorizes, and persists everything in one transaction. "
        "If the institution can't be determined from the file alone "
        "(Capital One and Discover share an identical header), responds "
        "409 with candidate institution codes — retry the same upload "
        "with the 'institution' field set to disambiguate."
    ),
)
async def upload_file(
    file: UploadFile = File(..., description="The CSV file to ingest."),
    institution: str | None = Form(
        None,
        description=(
            "Optional institution code (e.g. 'capital_one', 'discover') that "
            "always overrides auto-detection. Required to resolve a 409 "
            "AMBIGUOUS_INSTITUTION response."
        ),
    ),
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BatchDetail:
    filename = file.filename or ""
    file_bytes = await file.read()

    try:
        outcome = ingest_file(
            db,
            workspace_id=ws.id,
            filename=filename,
            file_bytes=file_bytes,
            institution=institution,
        )
    except InvalidFileExtensionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_EXTENSION",
                "filename": exc.filename,
                "message": "Only .csv files (any case) are supported.",
            },
        ) from exc
    except UnknownInstitutionCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNKNOWN_INSTITUTION",
                "institution": exc.institution,
                "message": f"Unknown institution code: {exc.institution!r}.",
            },
        ) from exc
    except AmbiguousInstitutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AMBIGUOUS_INSTITUTION",
                "candidates": list(exc.candidates),
                "message": (
                    "Could not determine the institution from the file's "
                    "header or filename. Retry the upload with an explicit "
                    "'institution' field set to one of the candidates."
                ),
            },
        ) from exc
    except UnknownFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNKNOWN_FORMAT",
                "header": list(exc.header),
                "message": "This CSV header doesn't match any known bank format.",
            },
        ) from exc

    return _batch_to_detail(outcome.batch)


@router.get(
    "",
    response_model=list[BatchSummary],
    summary="List recent ingest batches",
    description="Returns ingest batches newest-first, most recent uploads at the top.",
)
def list_batches(
    limit: int = 50,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> list[BatchSummary]:
    batches = (
        db.execute(
            select(IngestBatch)
            .where(IngestBatch.workspace_id == ws.id)
            .order_by(IngestBatch.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_batch_to_summary(b) for b in batches]


@router.get(
    "/{batch_id}",
    response_model=BatchDetail,
    summary="Get one ingest batch, including its parse failures",
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BatchDetail:
    batch = db.get(IngestBatch, batch_id)
    if batch is None or batch.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return _batch_to_detail(batch)
