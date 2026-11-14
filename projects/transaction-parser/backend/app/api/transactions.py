"""Transaction query and recategorize endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Account, Category, Transaction
from app.schemas.transactions import (
    MonthOption,
    SortOrder,
    TransactionListResponse,
    TransactionPatch,
    TransactionRead,
    TransactionSortField,
)
from app.services.cache import bump_generation

router = APIRouter(prefix="/transactions", tags=["transactions"])

_SORT_COLUMNS: dict[str, object] = {
    "txn_date": Transaction.txn_date,
    "amount": Transaction.amount,
    "description": Transaction.description,
    "category": Category.name,
}


def _transaction_to_read(txn: Transaction) -> TransactionRead:
    return TransactionRead(
        id=txn.id,
        account_id=txn.account_id,
        account_name=txn.account.display_name,
        batch_id=txn.batch_id,
        txn_date=txn.txn_date,
        posted_date=txn.posted_date,
        description=txn.description,
        amount=txn.amount,
        bank_category=txn.bank_category,
        category_id=txn.category_id,
        category_name=txn.category.name if txn.category else None,
        category_source=txn.category_source,
        is_recurring=txn.is_recurring,
        recurrence=txn.recurrence,
        created_at=txn.created_at,
    )


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List and filter transactions",
    description=(
        "Filterable, sortable, paginated transaction listing. By default "
        "(`include_excluded=false`) transactions whose category is marked "
        "`excluded_from_analytics` (e.g. 'Payments & Transfers', 'Income') "
        "are left out, matching the analytics endpoints' default. Pass "
        "`include_excluded=true` to see everything."
    ),
)
def list_transactions(
    date_from: date | None = Query(None, description="Inclusive lower bound on txn_date."),
    date_to: date | None = Query(None, description="Inclusive upper bound on txn_date."),
    account_ids: list[int] | None = Query(None, description="Filter to one or more account ids."),
    category_ids: list[int] | None = Query(None, description="Filter to one or more category ids."),
    q: str | None = Query(None, description="Case-insensitive substring match on description."),
    recurring_only: bool = Query(False, description="Only transactions flagged is_recurring=true."),
    include_excluded: bool = Query(
        False,
        description=(
            "When false (default), excludes transactions whose category has "
            "excluded_from_analytics=true (transfers, income). When true, "
            "includes everything."
        ),
    ),
    sort: TransactionSortField = Query("txn_date", description="Field to sort by."),
    order: SortOrder = Query("desc", description="Sort direction."),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    stmt = select(Transaction).join(Account, Transaction.account_id == Account.id)
    stmt = stmt.outerjoin(Category, Transaction.category_id == Category.id)

    if date_from is not None:
        stmt = stmt.where(Transaction.txn_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.txn_date <= date_to)
    if account_ids:
        stmt = stmt.where(Transaction.account_id.in_(account_ids))
    if category_ids:
        stmt = stmt.where(Transaction.category_id.in_(category_ids))
    if q:
        stmt = stmt.where(Transaction.description.ilike(f"%{q}%"))
    if recurring_only:
        stmt = stmt.where(Transaction.is_recurring.is_(True))
    if not include_excluded:
        stmt = stmt.where(func.coalesce(Category.excluded_from_analytics, False).is_(False))

    count_stmt = select(func.count()).select_from(stmt.with_only_columns(Transaction.id).subquery())
    total = db.execute(count_stmt).scalar_one()

    sort_column = _SORT_COLUMNS[sort]
    order_column = sort_column.desc() if order == "desc" else sort_column.asc()
    stmt = stmt.order_by(order_column, Transaction.id.desc()).limit(limit).offset(offset)

    rows = db.execute(stmt).scalars().all()
    items = [_transaction_to_read(t) for t in rows]

    return TransactionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/months",
    response_model=list[MonthOption],
    summary="List months that have at least one transaction",
    description=(
        "Computed with a single GROUP BY on txn_date in SQL — unlike deriving "
        "a min..max range client-side, this never reports a month that has no "
        "records. Descending (most recent first), matching how Records and "
        "the Time Series month-swipe both want to walk the list."
    ),
)
def list_months(db: Session = Depends(get_db)) -> list[MonthOption]:
    month_start = func.date_trunc("month", Transaction.txn_date)
    stmt = (
        select(month_start.label("month_start"))
        .distinct()
        .order_by(month_start.desc())
    )
    rows = db.execute(stmt).all()

    months: list[MonthOption] = []
    for (month_start_value,) in rows:
        year, month = month_start_value.year, month_start_value.month
        first_day = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        last_day = next_month.fromordinal(next_month.toordinal() - 1)
        key = f"{year}-{month:02d}"
        label = first_day.strftime("%b %Y")
        months.append(MonthOption(key=key, label=label, **{"from": first_day}, to=last_day))

    return months


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Manually recategorize and/or flag the recurrence of a single transaction",
    description=(
        "Setting category_id marks category_source='manual' (sticky against "
        "future keyword apply_to_existing operations). is_recurring/recurrence "
        "can be set independently of category_id in the same request."
    ),
)
def patch_transaction(
    transaction_id: int,
    payload: TransactionPatch,
    db: Session = Depends(get_db),
) -> TransactionRead:
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {payload.category_id} not found",
            )
        txn.category_id = category.id
        txn.category_source = "manual"

    if payload.is_recurring is not None:
        txn.is_recurring = payload.is_recurring
        txn.recurrence = payload.recurrence if payload.is_recurring else None

    db.commit()
    db.refresh(txn)
    bump_generation()
    return _transaction_to_read(txn)
