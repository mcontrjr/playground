"""Category CRUD, keyword management, and impact-preview endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bucket, Category, CategoryKeyword, ClashDismissal, Transaction
from app.schemas.categories import (
    CategoryCreate,
    CategoryDeleteResponse,
    CategoryKeywordCreate,
    CategoryKeywordCreateResponse,
    CategoryKeywordDeleteResponse,
    CategoryKeywordRead,
    CategoryPatch,
    CategoryPatchResponse,
    CategoryRead,
    ClashClaim,
    ClashDismissRequest,
    ClashDismissalListResponse,
    ClashDismissalRead,
    ClashListResponse,
    ClashResolveRequest,
    ClashResolveResponse,
    ErrorDetail,
    ImpactPreviewBreakdownEntry,
    ImpactPreviewRequest,
    ImpactPreviewResponse,
    ImpactPreviewTransaction,
    ReprioritizeMove,
    ReprioritizeRequest,
    ReprioritizeResponse,
    TransactionClashRead,
)
from app.services.audit_service import record_event
from app.services.cache import bump_generation
from app.services.categorizer import UNCATEGORIZED_CATEGORY_NAME
from app.services.category_service import (
    CategoryMove,
    apply_moves,
    clashes_for_keyword,
    count_dismissed_clashes,
    dismiss_clash,
    find_clashes,
    preview_add_keyword,
    preview_delete_category,
    preview_remove_keyword,
    preview_reprioritize,
    resolve_clash,
    undismiss_clash,
)

router = APIRouter(prefix="/categories", tags=["categories"])

OTHER_BUCKET_NAME = "OTHER"


def _category_to_read(category: Category, transaction_count: int) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        is_system=category.is_system,
        excluded_from_analytics=category.excluded_from_analytics,
        priority=category.priority,
        bucket_id=category.bucket_id,
        group=category.bucket.name,
        keywords=[CategoryKeywordRead.model_validate(k) for k in category.keywords],
        transaction_count=transaction_count,
    )


def _get_uncategorized(db: Session) -> Category:
    category = db.execute(
        select(Category).where(Category.name == UNCATEGORIZED_CATEGORY_NAME)
    ).scalar_one_or_none()
    if category is None:  # pragma: no cover - only if seed hasn't run
        raise RuntimeError("Uncategorized system category missing — has seed run?")
    return category


def _get_other_bucket(db: Session) -> Bucket:
    bucket = db.execute(
        select(Bucket).where(Bucket.name == OTHER_BUCKET_NAME)
    ).scalar_one_or_none()
    if bucket is None:  # pragma: no cover - only if seed hasn't run
        raise RuntimeError("OTHER system bucket missing — has seed run?")
    return bucket


def _resolve_bucket(db: Session, bucket_id: int | None) -> Bucket:
    if bucket_id is None:
        return _get_other_bucket(db)
    bucket = db.get(Bucket, bucket_id)
    if bucket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Bucket {bucket_id} not found"
        )
    return bucket


def _moves_to_breakdown(
    db: Session, moves: list[CategoryMove]
) -> list[ImpactPreviewBreakdownEntry]:
    category_ids = {m.transaction.category_id for m in moves} | {m.new_category_id for m in moves}
    category_ids.discard(None)
    categories = {
        c.id: c
        for c in db.execute(select(Category).where(Category.id.in_(category_ids))).scalars().all()
    }

    counts: dict[tuple[int | None, int | None], int] = {}
    for move in moves:
        key = (move.transaction.category_id, move.new_category_id)
        counts[key] = counts.get(key, 0) + 1

    breakdown = []
    for (from_id, to_id), count in sorted(counts.items(), key=lambda kv: -kv[1]):
        from_cat = categories.get(from_id) if from_id is not None else None
        to_cat = categories.get(to_id) if to_id is not None else None
        breakdown.append(
            ImpactPreviewBreakdownEntry(
                from_category_id=from_id,
                from_category=from_cat.name if from_cat else None,
                to_category_id=to_id,
                to_category=to_cat.name if to_cat else None,
                count=count,
            )
        )
    return breakdown


def _moves_to_sample(
    db: Session, moves: list[CategoryMove]
) -> list[ImpactPreviewTransaction]:
    category_ids = {m.transaction.category_id for m in moves} | {m.new_category_id for m in moves}
    category_ids.discard(None)
    categories = {
        c.id: c
        for c in db.execute(select(Category).where(Category.id.in_(category_ids))).scalars().all()
    }
    sample = []
    for move in moves[:20]:
        from_cat = categories.get(move.transaction.category_id) if move.transaction.category_id else None
        to_cat = categories.get(move.new_category_id) if move.new_category_id else None
        sample.append(
            ImpactPreviewTransaction(
                id=move.transaction.id,
                description=move.transaction.description,
                current_category_id=move.transaction.category_id,
                current_category_name=from_cat.name if from_cat else None,
                new_category_id=move.new_category_id,
                new_category_name=to_cat.name if to_cat else None,
            )
        )
    return sample


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="List categories",
    description="All categories with their keywords, system/exclusion flags, priority, and transaction counts.",
)
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    categories = db.execute(select(Category).order_by(Category.priority)).scalars().all()
    counts = dict(
        db.execute(
            select(Transaction.category_id, func.count())
            .group_by(Transaction.category_id)
        ).all()
    )
    return [_category_to_read(c, counts.get(c.id, 0)) for c in categories]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    responses={
        409: {
            "model": ErrorDetail,
            "description": "A category with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "CATEGORY_NAME_TAKEN",
                            "message": "A category named 'Subscriptions' already exists.",
                        }
                    }
                }
            },
        },
    },
)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    existing = db.execute(select(Category).where(Category.name == payload.name)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CATEGORY_NAME_TAKEN",
                "message": f"A category named {payload.name!r} already exists.",
            },
        )

    priority = payload.priority
    if priority is None:
        max_priority = db.execute(select(func.max(Category.priority))).scalar_one_or_none()
        priority = (max_priority or 0) + 1

    bucket = _resolve_bucket(db, payload.bucket_id)

    category = Category(
        name=payload.name,
        is_system=False,
        excluded_from_analytics=payload.excluded_from_analytics,
        priority=priority,
        bucket_id=bucket.id,
    )
    db.add(category)
    db.flush()

    record_event(
        db,
        event_type="category.created",
        entity_type="category",
        entity_id=category.id,
        description=f"Created category {category.name!r} in bucket {bucket.name!r}.",
        payload={"name": category.name, "bucket_id": bucket.id, "bucket": bucket.name},
    )

    db.commit()
    db.refresh(category)
    bump_generation()
    return _category_to_read(category, 0)


@router.patch(
    "/{category_id}",
    response_model=CategoryPatchResponse,
    summary="Rename a category / edit priority or exclusion flag",
    description="Only provided fields are changed. Returns the affected transaction count (rows currently assigned to this category).",
    responses={
        409: {
            "model": ErrorDetail,
            "description": "Another category already has the requested name.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "CATEGORY_NAME_TAKEN",
                            "message": "A category named 'Dining & Coffee' already exists.",
                        }
                    }
                }
            },
        },
    },
)
def patch_category(
    category_id: int,
    payload: CategoryPatch,
    db: Session = Depends(get_db),
) -> CategoryPatchResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if payload.name is not None and payload.name != category.name:
        name_conflict = db.execute(
            select(Category).where(Category.name == payload.name, Category.id != category_id)
        ).scalar_one_or_none()
        if name_conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "CATEGORY_NAME_TAKEN",
                    "message": f"A category named {payload.name!r} already exists.",
                },
            )
        old_name = category.name
        category.name = payload.name
        record_event(
            db,
            event_type="category.renamed",
            entity_type="category",
            entity_id=category.id,
            description=f"Renamed category {old_name!r} to {payload.name!r}.",
            payload={"from": old_name, "to": payload.name},
        )

    if payload.priority is not None:
        category.priority = payload.priority
    if payload.excluded_from_analytics is not None:
        category.excluded_from_analytics = payload.excluded_from_analytics
    if payload.bucket_id is not None and payload.bucket_id != category.bucket_id:
        new_bucket = _resolve_bucket(db, payload.bucket_id)
        old_bucket = db.get(Bucket, category.bucket_id)
        old_bucket_name = old_bucket.name if old_bucket is not None else None
        category.bucket_id = new_bucket.id
        record_event(
            db,
            event_type="category.bucket_changed",
            entity_type="category",
            entity_id=category.id,
            description=(
                f"Moved category {category.name!r} from bucket "
                f"{old_bucket_name!r} to bucket {new_bucket.name!r}."
            ),
            payload={"from_bucket_id": old_bucket.id if old_bucket else None, "to_bucket_id": new_bucket.id},
        )

    db.commit()
    db.refresh(category)
    bump_generation()

    affected_count = db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.category_id == category.id)
    ).scalar_one()

    return CategoryPatchResponse(
        category=_category_to_read(category, affected_count),
        affected_transaction_count=affected_count,
    )


@router.delete(
    "/{category_id}",
    response_model=CategoryDeleteResponse,
    summary="Delete a category",
    description=(
        "System categories cannot be deleted (409). Deleting a regular "
        "category reassigns its transactions to Uncategorized and cascades "
        "its keywords."
    ),
    responses={
        409: {
            "model": ErrorDetail,
            "description": "This category is a system category and cannot be deleted.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "SYSTEM_CATEGORY_UNDELETABLE",
                            "message": "'Uncategorized' is a system category and cannot be deleted.",
                        }
                    }
                }
            },
        },
    },
)
def delete_category(
    category_id: int,
    rematch: bool = Query(
        False,
        description=(
            "Re-run the remaining rules over this category's transactions "
            "instead of parking them all in Uncategorized. Rows nothing "
            "matches still land in Uncategorized; manual/bulk rows are "
            "never re-matched."
        ),
    ),
    db: Session = Depends(get_db),
) -> CategoryDeleteResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SYSTEM_CATEGORY_UNDELETABLE",
                "message": f"{category.name!r} is a system category and cannot be deleted.",
            },
        )

    uncategorized = _get_uncategorized(db)

    reassigned_count = db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.category_id == category.id)
    ).scalar_one()

    # Compute re-match targets *before* the delete, while this category's
    # keywords still exist to be excluded from the hypothetical snapshot.
    rematch_moves: list[CategoryMove] = []
    if rematch:
        rematch_moves = preview_delete_category(db, category_id=category.id)

    # Park everything on Uncategorized first: rows the rules don't claim
    # (and manual/bulk rows, which re-matching deliberately skips) still
    # need to come off the category about to be deleted.
    db.execute(
        Transaction.__table__.update()
        .where(Transaction.category_id == category.id)
        .values(category_id=uncategorized.id, category_source="default", matched_keyword=None)
    )

    # Then place the rows the remaining rules actually claim.
    rematched_count = 0
    if rematch:
        rematched_count = apply_moves(
            db, [m for m in rematch_moves if m.new_category_id != uncategorized.id]
        )

    deleted_name = category.name
    db.delete(category)  # cascades category_keywords

    record_event(
        db,
        event_type="category.deleted",
        entity_type="category",
        entity_id=category_id,
        description=(
            f"Deleted category {deleted_name!r}; reassigned its transactions "
            f"to {uncategorized.name!r}"
            + (f", re-matching {rematched_count} by keyword." if rematch else ".")
        ),
        payload={"name": deleted_name, "rematch": rematch},
        affected_count=reassigned_count,
    )

    db.commit()
    bump_generation()

    return CategoryDeleteResponse(
        deleted_category_id=category_id,
        reassigned_transaction_count=reassigned_count,
        rematched_transaction_count=rematched_count,
    )


@router.post(
    "/impact-preview",
    response_model=ImpactPreviewResponse,
    summary="Dry-run a keyword add/remove",
    description=(
        "Reports what would happen if a keyword were added to or removed "
        "from a category, WITHOUT making any changes. Reuses the full "
        "categorizer precedence (transfer-first, then priority, then "
        "keyword length) so the preview exactly matches what apply_to_existing "
        "would do. Manual recategorizations are never candidates."
    ),
)
def impact_preview(
    payload: ImpactPreviewRequest, db: Session = Depends(get_db)
) -> ImpactPreviewResponse:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if payload.action == "add_keyword":
        moves = preview_add_keyword(db, category_id=payload.category_id, keyword=payload.keyword)
    else:
        moves = preview_remove_keyword(db, category_id=payload.category_id, keyword=payload.keyword)

    return ImpactPreviewResponse(
        affected_count=len(moves),
        sample=_moves_to_sample(db, moves),
        breakdown=_moves_to_breakdown(db, moves),
    )


@router.post(
    "/{category_id}/keywords",
    response_model=CategoryKeywordCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a keyword to a category",
    description=(
        "Keywords are globally unique across all categories (409 with the "
        "owning category on conflict). When apply_to_existing is true, "
        "re-runs the same logic as /impact-preview and applies it, setting "
        "category_source='keyword' on affected (non-manual) rows."
    ),
    responses={
        409: {
            "model": ErrorDetail,
            "description": "This keyword already belongs to another category.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "KEYWORD_ALREADY_CLAIMED",
                            "message": "Keyword 'STARBUCKS' already belongs to 'FOOD'.",
                            "owning_category_id": 8,
                            "owning_category_name": "FOOD",
                        }
                    }
                }
            },
        },
    },
)
def add_keyword(
    category_id: int,
    payload: CategoryKeywordCreate,
    db: Session = Depends(get_db),
) -> CategoryKeywordCreateResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    keyword_upper = payload.keyword.upper().strip()
    existing = db.execute(
        select(CategoryKeyword).where(CategoryKeyword.keyword == keyword_upper)
    ).scalar_one_or_none()
    if existing is not None:
        owner = db.get(Category, existing.category_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "KEYWORD_ALREADY_CLAIMED",
                "message": f"Keyword {keyword_upper!r} already belongs to {owner.name!r}.",
                "owning_category_id": owner.id,
                "owning_category_name": owner.name,
            },
        )

    keyword_row = CategoryKeyword(category_id=category_id, keyword=keyword_upper)
    db.add(keyword_row)
    db.flush()

    applied_count = 0
    if payload.apply_to_existing:
        moves = preview_add_keyword(db, category_id=category_id, keyword=keyword_upper)
        applied_count = apply_moves(db, moves)

    record_event(
        db,
        event_type="keyword.added",
        entity_type="category",
        entity_id=category.id,
        description=f"Added keyword {keyword_upper!r} to category {category.name!r}.",
        payload={"keyword": keyword_upper, "category_id": category.id},
        affected_count=applied_count,
    )

    db.commit()
    db.refresh(keyword_row)
    bump_generation()

    return CategoryKeywordCreateResponse(
        keyword=CategoryKeywordRead.model_validate(keyword_row),
        applied_count=applied_count,
    )


@router.delete(
    "/{category_id}/keywords/{keyword_id}",
    response_model=CategoryKeywordDeleteResponse,
    summary="Remove a keyword from a category",
    description=(
        "With ?reapply=true, re-categorizes (via full categorizer "
        "precedence) every non-manual transaction that was matched by this "
        "keyword; manual recategorizations are left untouched."
    ),
)
def delete_keyword(
    category_id: int,
    keyword_id: int,
    reapply: bool = Query(False, description="Re-categorize affected transactions after removal."),
    db: Session = Depends(get_db),
) -> CategoryKeywordDeleteResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    keyword_row = db.get(CategoryKeyword, keyword_id)
    if keyword_row is None or keyword_row.category_id != category_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")

    moves: list[CategoryMove] = []
    if reapply:
        moves = preview_remove_keyword(db, category_id=category_id, keyword=keyword_row.keyword)

    deleted_keyword_text = keyword_row.keyword
    db.delete(keyword_row)
    db.flush()

    reapplied_count = 0
    if reapply:
        reapplied_count = apply_moves(db, moves)

    record_event(
        db,
        event_type="keyword.removed",
        entity_type="category",
        entity_id=category.id,
        description=f"Removed keyword {deleted_keyword_text!r} from category {category.name!r}.",
        payload={"keyword": deleted_keyword_text, "category_id": category.id},
        affected_count=reapplied_count,
    )

    db.commit()
    bump_generation()

    return CategoryKeywordDeleteResponse(
        deleted_keyword_id=keyword_id, reapplied_count=reapplied_count
    )


# --- Clash reconciliation ---------------------------------------------------


@router.get(
    "/clashes",
    response_model=ClashListResponse,
    summary="Transactions claimed by more than one category",
    description=(
        "A clash is a description whose keywords match two or more "
        "categories. The categorizer always resolves it silently "
        "(transfer-first, then priority ascending, then keyword length), "
        "so this endpoint exposes those decisions for review.\n\n"
        "By default only unsettled rows are listed — manual/bulk rows are "
        "the user's final say and are never actionable. Rows flagged "
        "transfer_decided cannot be changed by any priority reorder, since "
        "the transfer stage runs before priority is consulted."
    ),
)
def list_clashes(
    include_settled: bool = Query(
        default=False, description="Also list manual/bulk rows (reporting only)."
    ),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ClashListResponse:
    clashes = find_clashes(db, include_settled=include_settled)
    all_with_settled = find_clashes(db, include_settled=True)
    settled_count = sum(1 for c in all_with_settled if c.is_settled)

    categories = {c.id: c for c in db.execute(select(Category)).scalars().all()}

    items: list[TransactionClashRead] = []
    for clash in clashes[:limit]:
        txn = clash.transaction
        winner = clash.report.winner
        items.append(
            TransactionClashRead(
                transaction_id=txn.id,
                description=txn.description,
                txn_date=txn.txn_date,
                amount=txn.amount,
                current_category_id=txn.category_id,
                current_category_name=(
                    categories[txn.category_id].name if txn.category_id in categories else None
                ),
                category_source=txn.category_source,
                is_settled=clash.is_settled,
                transfer_decided=clash.report.transfer_decided,
                claims=[
                    ClashClaim(
                        category_id=claim.category_id,
                        category_name=categories[claim.category_id].name,
                        keyword=claim.keyword,
                        priority=categories[claim.category_id].priority,
                        stage=claim.stage,
                        is_winner=(winner is not None and claim is winner),
                    )
                    for claim in clash.report.claims
                    if claim.category_id in categories
                ],
            )
        )

    return ClashListResponse(
        total=len(clashes),
        settled_count=settled_count,
        dismissed_count=count_dismissed_clashes(db),
        items=items,
    )


@router.post(
    "/clashes/preview-keyword",
    response_model=ClashListResponse,
    summary="Clashes a not-yet-added keyword would create",
    description=(
        "Dry run for the add-keyword flow: reports rows that would be "
        "claimed by BOTH this category (via the new keyword) and some "
        "other category, i.e. where priority — not the user — would "
        "decide. Writes nothing. Settled rows are excluded."
    ),
)
def preview_keyword_clashes(
    payload: ImpactPreviewRequest,
    db: Session = Depends(get_db),
) -> ClashListResponse:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {payload.category_id} not found",
        )

    clashes = clashes_for_keyword(
        db, category_id=payload.category_id, keyword=payload.keyword
    )
    categories = {c.id: c for c in db.execute(select(Category)).scalars().all()}

    items: list[TransactionClashRead] = []
    for clash in clashes[:100]:
        txn = clash.transaction
        winner = clash.report.winner
        items.append(
            TransactionClashRead(
                transaction_id=txn.id,
                description=txn.description,
                txn_date=txn.txn_date,
                amount=txn.amount,
                current_category_id=txn.category_id,
                current_category_name=(
                    categories[txn.category_id].name if txn.category_id in categories else None
                ),
                category_source=txn.category_source,
                is_settled=False,
                transfer_decided=clash.report.transfer_decided,
                claims=[
                    ClashClaim(
                        category_id=claim.category_id,
                        category_name=categories[claim.category_id].name,
                        keyword=claim.keyword,
                        priority=categories[claim.category_id].priority,
                        stage=claim.stage,
                        is_winner=(winner is not None and claim is winner),
                    )
                    for claim in clash.report.claims
                    if claim.category_id in categories
                ],
            )
        )

    # Nothing above writes, but the hypothetical snapshot touched the
    # session — drop it so no speculative state can be flushed later.
    db.rollback()
    return ClashListResponse(total=len(clashes), settled_count=0, items=items)


@router.post(
    "/clashes/resolve",
    response_model=ClashResolveResponse,
    summary="Settle a clash with the user's explicit choice",
    description=(
        "Pins the given transactions to the chosen category with "
        "category_source='manual', which is permanently sticky: no "
        "later keyword add, priority reorder, or recategorize-all pass "
        "will move them again.\n\n"
        "scope='all_matching' additionally pins every other unsettled "
        "row whose normalized description contains `keyword`, so a "
        "recurring merchant can be settled in one action."
    ),
    responses={404: {"model": ErrorDetail}, 422: {"model": ErrorDetail}},
)
def resolve_clashes(
    payload: ClashResolveRequest,
    db: Session = Depends(get_db),
) -> ClashResolveResponse:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {payload.category_id} not found",
        )

    transaction_ids = list(payload.transaction_ids)

    if payload.scope == "all_matching":
        if not payload.keyword or not payload.keyword.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="keyword is required when scope='all_matching'",
            )
        keyword_upper = payload.keyword.upper().strip()
        siblings = (
            db.execute(
                select(Transaction.id)
                .where(Transaction.category_source.not_in(["manual", "bulk"]))
                .where(Transaction.normalized_description.like(f"%{keyword_upper}%"))
            )
            .scalars()
            .all()
        )
        transaction_ids = list(dict.fromkeys([*transaction_ids, *siblings]))

    resolved = resolve_clash(db, transaction_ids=transaction_ids, category_id=category.id)

    record_event(
        db,
        event_type="category.clash_resolved",
        entity_type="category",
        entity_id=category.id,
        description=(
            f"Resolved {resolved} clashing transaction(s) to {category.name!r} "
            f"(scope={payload.scope})."
        ),
        payload={
            "category_id": category.id,
            "scope": payload.scope,
            "keyword": payload.keyword,
        },
        affected_count=resolved,
    )

    db.commit()
    bump_generation()
    return ClashResolveResponse(
        resolved_count=resolved, category_id=category.id, category_name=category.name
    )


@router.post(
    "/reprioritize",
    response_model=ReprioritizeResponse,
    summary="Re-prioritize categories (lower matches first)",
    description=(
        "Sets new priority values and, when dry_run=false, re-runs the "
        "categorizer so existing non-sticky rows reflect the new order — "
        "without this, a priority edit silently changes nothing for rows "
        "already ingested.\n\n"
        "Defaults to dry_run=true: priority is global, so a reorder meant "
        "to fix one merchant can move unrelated rows that share a keyword. "
        "Manual and bulk rows are never moved."
    ),
    responses={404: {"model": ErrorDetail}},
)
def reprioritize(
    payload: ReprioritizeRequest,
    db: Session = Depends(get_db),
) -> ReprioritizeResponse:
    priorities = {int(k): int(v) for k, v in payload.priorities.items()}

    categories = {c.id: c for c in db.execute(select(Category)).scalars().all()}
    missing = [cid for cid in priorities if cid not in categories]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown category id(s): {sorted(missing)}",
        )

    moves = preview_reprioritize(db, priorities=priorities)
    candidate_count = len(moves)

    # Names resolved before mutating, so "from" reflects the prior state.
    names = {cid: c.name for cid, c in categories.items()}
    reported = [
        ReprioritizeMove(
            transaction_id=m.transaction.id,
            description=m.transaction.description,
            from_category_name=names.get(m.transaction.category_id),
            to_category_name=names.get(m.new_category_id),
        )
        for m in moves[:200]
    ]

    if payload.dry_run:
        db.rollback()
        return ReprioritizeResponse(
            dry_run=True,
            candidate_count=candidate_count,
            affected_count=0,
            moves=reported,
        )

    for cid, new_priority in priorities.items():
        categories[cid].priority = new_priority
    db.flush()

    # Recompute against the now-committed ordering rather than reusing the
    # dry-run moves, so the applied result can't drift from the real rules.
    final_moves = preview_reprioritize(db, priorities={})
    for cid, new_priority in priorities.items():
        categories[cid].priority = new_priority
    affected_count = apply_moves(db, final_moves)

    record_event(
        db,
        event_type="category.reprioritized",
        entity_type="category",
        entity_id=None,
        description=(
            f"Re-prioritized {len(priorities)} category(ies); "
            f"{affected_count} transaction(s) recategorized."
        ),
        payload={"priorities": {str(k): v for k, v in priorities.items()}},
        affected_count=affected_count,
    )

    db.commit()
    bump_generation()
    return ReprioritizeResponse(
        dry_run=False,
        candidate_count=candidate_count,
        affected_count=affected_count,
        moves=reported,
    )


@router.get(
    "/{category_id}/delete-preview",
    response_model=ImpactPreviewResponse,
    summary="Where this category's transactions would land if it were deleted",
    description=(
        "Dry run for the delete flow. Deleting a category removes its "
        "keywords too, so its rows have to go somewhere — this reports "
        "where the *remaining* rules would actually place each one, "
        "which is often a real category rather than Uncategorized.\n\n"
        "Writes nothing. Manual/bulk rows are excluded: their category "
        "was chosen by a person, so the rules don't re-decide them "
        "(the delete still moves them off the doomed category)."
    ),
    responses={404: {"model": ErrorDetail}},
)
def delete_category_preview(
    category_id: int, db: Session = Depends(get_db)
) -> ImpactPreviewResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # System categories can't be deleted (DELETE returns 409), and the
    # categorizer requires Payments & Transfers / Uncategorized to exist
    # — previewing their removal would build an unusable rule set.
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SYSTEM_CATEGORY_UNDELETABLE",
                "message": f"{category.name!r} is a system category and cannot be deleted.",
            },
        )

    moves = preview_delete_category(db, category_id=category_id)
    breakdown = _moves_to_breakdown(db, moves)
    sample = _moves_to_sample(db, moves)

    # The hypothetical snapshot touched the session; drop it so nothing
    # speculative can be flushed later.
    db.rollback()
    return ImpactPreviewResponse(
        affected_count=len(moves), breakdown=breakdown, sample=sample
    )


@router.get(
    "/clashes/dismissals",
    response_model=ClashDismissalListResponse,
    summary="Conflicts dismissed as correct",
    description=(
        "Dismissals hide conflicts the user judged fine as-is. A "
        "rule-level dismissal (transaction_id null) covers every current "
        "and future row where those two categories compete; a row-level "
        "one covers a single record.\n\n"
        "`hidden_count` is counted against live transactions, so one rule "
        "covering nine rows reports nine — what 'N dismissed' should mean."
    ),
)
def list_clash_dismissals(db: Session = Depends(get_db)) -> ClashDismissalListResponse:
    dismissals = db.execute(select(ClashDismissal)).scalars().all()
    categories = {c.id: c for c in db.execute(select(Category)).scalars().all()}

    # Attribute hidden rows to the dismissal that covers them, so each
    # row in the UI can say how much it is actually suppressing.
    hidden_by_dismissal: dict[int, int] = {d.id: 0 for d in dismissals}
    for clash in find_clashes(db, include_settled=True, include_dismissed=True):
        winner = clash.report.winner
        if winner is None:
            continue
        losers = {
            c.category_id for c in clash.report.claims if c.category_id != winner.category_id
        }
        for d in dismissals:
            if d.winner_category_id != winner.category_id:
                continue
            if d.loser_category_id not in losers:
                continue
            if d.transaction_id is not None and d.transaction_id != clash.transaction.id:
                continue
            hidden_by_dismissal[d.id] += 1

    items = [
        ClashDismissalRead(
            id=d.id,
            winner_category_id=d.winner_category_id,
            winner_category_name=categories[d.winner_category_id].name
            if d.winner_category_id in categories
            else "(deleted)",
            loser_category_id=d.loser_category_id,
            loser_category_name=categories[d.loser_category_id].name
            if d.loser_category_id in categories
            else "(deleted)",
            transaction_id=d.transaction_id,
            note=d.note,
            hidden_count=hidden_by_dismissal.get(d.id, 0),
        )
        for d in dismissals
    ]

    return ClashDismissalListResponse(
        total=len(items),
        hidden_total=count_dismissed_clashes(db),
        items=items,
    )


@router.post(
    "/clashes/dismiss",
    response_model=ClashDismissalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Dismiss a conflict as correct as-is",
    description=(
        "Stops listing a conflict without touching the transaction's "
        "category — the categorizer's choice was already right.\n\n"
        "Omit transaction_id to dismiss the pairing itself, which also "
        "covers rows imported later. Idempotent: re-dismissing the same "
        "scope returns the existing dismissal."
    ),
    responses={404: {"model": ErrorDetail}},
)
def dismiss_clash_endpoint(
    payload: ClashDismissRequest,
    db: Session = Depends(get_db),
) -> ClashDismissalRead:
    categories = {c.id: c for c in db.execute(select(Category)).scalars().all()}
    for cid in (payload.winner_category_id, payload.loser_category_id):
        if cid not in categories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {cid} not found"
            )
    if payload.transaction_id is not None and db.get(Transaction, payload.transaction_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {payload.transaction_id} not found",
        )

    dismissal = dismiss_clash(
        db,
        winner_category_id=payload.winner_category_id,
        loser_category_id=payload.loser_category_id,
        transaction_id=payload.transaction_id,
        note=payload.note,
    )

    winner_name = categories[payload.winner_category_id].name
    loser_name = categories[payload.loser_category_id].name
    scope = "this record" if payload.transaction_id else "all records"
    record_event(
        db,
        event_type="category.clash_dismissed",
        entity_type="category",
        entity_id=payload.winner_category_id,
        description=(
            f"Dismissed conflict {winner_name!r} over {loser_name!r} ({scope})."
        ),
        payload={
            "winner": winner_name,
            "loser": loser_name,
            "transaction_id": payload.transaction_id,
        },
    )

    db.commit()
    db.refresh(dismissal)
    bump_generation()

    return ClashDismissalRead(
        id=dismissal.id,
        winner_category_id=dismissal.winner_category_id,
        winner_category_name=winner_name,
        loser_category_id=dismissal.loser_category_id,
        loser_category_name=loser_name,
        transaction_id=dismissal.transaction_id,
        note=dismissal.note,
        hidden_count=0,
    )


@router.delete(
    "/clashes/dismissals/{dismissal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Undo a dismissal",
    description="Returns the conflicts it was hiding to the review queue.",
    responses={404: {"model": ErrorDetail}},
)
def undismiss_clash_endpoint(dismissal_id: int, db: Session = Depends(get_db)) -> None:
    if not undismiss_clash(db, dismissal_id=dismissal_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dismissal not found")

    record_event(
        db,
        event_type="category.clash_undismissed",
        entity_type="category",
        entity_id=None,
        description="Restored a dismissed conflict to the review queue.",
        payload={"dismissal_id": dismissal_id},
    )
    db.commit()
    bump_generation()
