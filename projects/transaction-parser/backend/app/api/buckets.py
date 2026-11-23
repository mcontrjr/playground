"""Bucket CRUD. OTHER is the permanent, undeletable, unrenamable
fallback bucket every category lands in by default."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_workspace
from app.models import Bucket, Category, Workspace
from app.schemas.buckets import BucketCreate, BucketDeleteResult, BucketRead, BucketUpdate
from app.services.audit_service import record_event
from app.services.cache import bump_generation

router = APIRouter(prefix="/buckets", tags=["buckets"])

OTHER_BUCKET_NAME = "OTHER"


def _normalize_name(raw: str) -> str:
    return raw.strip().upper()


def _get_other_bucket(db: Session, workspace_id: int) -> Bucket:
    bucket = db.execute(
        select(Bucket).where(
            Bucket.workspace_id == workspace_id, Bucket.name == OTHER_BUCKET_NAME
        )
    ).scalar_one_or_none()
    if bucket is None:  # pragma: no cover - only if provisioning hasn't run
        raise RuntimeError("OTHER system bucket missing — has the workspace been provisioned?")
    return bucket


def _bucket_to_read(bucket: Bucket, category_count: int) -> BucketRead:
    return BucketRead(id=bucket.id, name=bucket.name, category_count=category_count)


@router.get(
    "",
    response_model=list[BucketRead],
    summary="List buckets",
    description="All buckets ordered by name, with how many categories currently belong to each.",
)
def list_buckets(
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> list[BucketRead]:
    buckets = (
        db.execute(
            select(Bucket).where(Bucket.workspace_id == ws.id).order_by(Bucket.name)
        )
        .scalars()
        .all()
    )
    counts = dict(
        db.execute(
            select(Category.bucket_id, func.count())
            .where(Category.workspace_id == ws.id)
            .group_by(Category.bucket_id)
        ).all()
    )
    return [_bucket_to_read(b, counts.get(b.id, 0)) for b in buckets]


@router.post(
    "",
    response_model=BucketRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bucket",
    description="Name is stripped and uppercased server-side.",
    responses={
        409: {"description": "A bucket with this name already exists."},
    },
)
def create_bucket(
    payload: BucketCreate,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BucketRead:
    name = _normalize_name(payload.name)
    existing = db.execute(
        select(Bucket).where(Bucket.workspace_id == ws.id, Bucket.name == name)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "BUCKET_NAME_TAKEN",
                "message": f"A bucket named {name!r} already exists.",
            },
        )

    bucket = Bucket(workspace_id=ws.id, name=name)
    db.add(bucket)
    db.flush()

    record_event(
        db,
        workspace_id=ws.id,
        event_type="bucket.created",
        entity_type="bucket",
        entity_id=bucket.id,
        description=f"Created bucket {name!r}.",
        payload={"name": name},
    )

    db.commit()
    db.refresh(bucket)
    bump_generation()
    return _bucket_to_read(bucket, 0)


@router.patch(
    "/{bucket_id}",
    response_model=BucketRead,
    summary="Rename a bucket",
    description="OTHER cannot be renamed.",
    responses={
        400: {"description": "OTHER cannot be renamed."},
        409: {"description": "Another bucket already has the requested name."},
    },
)
def patch_bucket(
    bucket_id: int,
    payload: BucketUpdate,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BucketRead:
    bucket = db.get(Bucket, bucket_id)
    if bucket is None or bucket.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")

    if bucket.name == OTHER_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "OTHER_BUCKET_PROTECTED",
                "message": "The OTHER bucket cannot be renamed.",
            },
        )

    new_name = _normalize_name(payload.name)
    if new_name != bucket.name:
        conflict = db.execute(
            select(Bucket).where(
                Bucket.workspace_id == ws.id,
                Bucket.name == new_name,
                Bucket.id != bucket_id,
            )
        ).scalar_one_or_none()
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "BUCKET_NAME_TAKEN",
                    "message": f"A bucket named {new_name!r} already exists.",
                },
            )

        old_name = bucket.name
        bucket.name = new_name

        record_event(
            db,
            workspace_id=ws.id,
            event_type="bucket.renamed",
            entity_type="bucket",
            entity_id=bucket.id,
            description=f"Renamed bucket {old_name!r} to {new_name!r}.",
            payload={"from": old_name, "to": new_name},
        )

    db.commit()
    db.refresh(bucket)
    bump_generation()

    category_count = db.execute(
        select(func.count()).select_from(Category).where(Category.bucket_id == bucket.id)
    ).scalar_one()
    return _bucket_to_read(bucket, category_count)


@router.delete(
    "/{bucket_id}",
    response_model=BucketDeleteResult,
    summary="Delete a bucket",
    description=(
        "OTHER cannot be deleted. Categories belonging to the deleted "
        "bucket are reassigned to `reassign_to_bucket_id` if given, else "
        "to OTHER."
    ),
    responses={
        400: {"description": "OTHER cannot be deleted, or reassign_to_bucket_id equals the bucket being deleted."},
    },
)
def delete_bucket(
    bucket_id: int,
    reassign_to_bucket_id: int | None = Query(
        None, description="Bucket to move this bucket's categories into. Defaults to OTHER."
    ),
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BucketDeleteResult:
    bucket = db.get(Bucket, bucket_id)
    if bucket is None or bucket.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")

    if bucket.name == OTHER_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "OTHER_BUCKET_PROTECTED",
                "message": "The OTHER bucket cannot be deleted.",
            },
        )

    if reassign_to_bucket_id is not None and reassign_to_bucket_id == bucket_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REASSIGN_TARGET_IS_SOURCE",
                "message": "reassign_to_bucket_id cannot equal the bucket being deleted.",
            },
        )

    if reassign_to_bucket_id is not None:
        target = db.get(Bucket, reassign_to_bucket_id)
        # Reject a target in another workspace: without this check the
        # categories would be moved across the tenancy boundary.
        if target is None or target.workspace_id != ws.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bucket {reassign_to_bucket_id} not found",
            )
    else:
        target = _get_other_bucket(db, ws.id)

    moved_count = db.execute(
        select(func.count()).select_from(Category).where(Category.bucket_id == bucket.id)
    ).scalar_one()

    db.execute(
        Category.__table__.update()
        .where(Category.bucket_id == bucket.id)
        .values(bucket_id=target.id)
    )

    deleted_name = bucket.name
    db.delete(bucket)

    record_event(
        db,
        workspace_id=ws.id,
        event_type="bucket.deleted",
        entity_type="bucket",
        entity_id=bucket_id,
        description=f"Deleted bucket {deleted_name!r}; moved its categories to {target.name!r}.",
        payload={"name": deleted_name, "reassigned_to_bucket_id": target.id},
        affected_count=moved_count,
    )

    db.commit()
    bump_generation()

    return BucketDeleteResult(
        moved_category_count=moved_count, reassigned_to_bucket_id=target.id
    )
