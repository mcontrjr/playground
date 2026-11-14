"""Category CRUD, keyword management, and impact-preview endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, CategoryKeyword, Transaction
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
    ErrorDetail,
    ImpactPreviewBreakdownEntry,
    ImpactPreviewRequest,
    ImpactPreviewResponse,
    ImpactPreviewTransaction,
)
from app.services.cache import bump_generation
from app.services.categorizer import UNCATEGORIZED_CATEGORY_NAME
from app.services.category_service import (
    CategoryMove,
    apply_moves,
    preview_add_keyword,
    preview_remove_keyword,
)

router = APIRouter(prefix="/categories", tags=["categories"])


def _category_to_read(category: Category, transaction_count: int) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        is_system=category.is_system,
        excluded_from_analytics=category.excluded_from_analytics,
        priority=category.priority,
        group=category.group,
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

    category = Category(
        name=payload.name,
        is_system=False,
        excluded_from_analytics=payload.excluded_from_analytics,
        priority=priority,
        group=payload.group or "Other",
    )
    db.add(category)
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
        category.name = payload.name

    if payload.priority is not None:
        category.priority = payload.priority
    if payload.excluded_from_analytics is not None:
        category.excluded_from_analytics = payload.excluded_from_analytics
    if payload.group is not None:
        category.group = payload.group

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
def delete_category(category_id: int, db: Session = Depends(get_db)) -> CategoryDeleteResponse:
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

    db.execute(
        Transaction.__table__.update()
        .where(Transaction.category_id == category.id)
        .values(category_id=uncategorized.id, category_source="default")
    )

    db.delete(category)  # cascades category_keywords
    db.commit()
    bump_generation()

    return CategoryDeleteResponse(
        deleted_category_id=category_id, reassigned_transaction_count=reassigned_count
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

    db.delete(keyword_row)
    db.flush()

    reapplied_count = 0
    if reapply:
        reapplied_count = apply_moves(db, moves)

    db.commit()
    bump_generation()

    return CategoryKeywordDeleteResponse(
        deleted_keyword_id=keyword_id, reapplied_count=reapplied_count
    )
