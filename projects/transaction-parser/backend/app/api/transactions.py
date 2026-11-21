"""Transaction query and recategorize endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Account, Category, Transaction
from app.schemas.transactions import (
    BulkRecategorizeRequest,
    BulkRecategorizeResponse,
    MonthOption,
    RecategorizeAllMove,
    RecategorizeAllRequest,
    RecategorizeAllResponse,
    SortOrder,
    TransactionFacets,
    TransactionListResponse,
    TransactionPatch,
    TransactionRead,
    TransactionSortField,
)
from app.services.audit_service import record_event
from app.services.cache import bump_generation
from app.services.category_service import apply_moves, preview_recategorize_all

# Cap on the per-move detail list in the response. The counts are always
# exact; only this itemization is truncated, so a full-DB catch-up pass
# can't return a multi-megabyte body.
_MAX_REPORTED_MOVES = 200

router = APIRouter(prefix="/transactions", tags=["transactions"])

_SORT_COLUMNS: dict[str, object] = {
    "txn_date": Transaction.txn_date,
    "amount": Transaction.amount,
    "description": Transaction.description,
    "category": Category.name,
}


def _apply_filters(
    stmt,
    *,
    date_from: date | None,
    date_to: date | None,
    account_ids: list[int] | None,
    category_ids: list[int] | None,
    q: str | None,
    recurring_only: bool,
    include_excluded: bool,
    exclude_category_ids: list[int] | None = None,
    outflows_only: bool = False,
    skip: str | None = None,
):
    """Applies the transaction list filters to `stmt`, optionally
    skipping one dimension (`skip` is 'date' | 'account' | 'category') —
    used by the facets endpoint to compute each dimension's available
    options against every *other* active filter, standard faceted-search
    style, so e.g. selecting an account doesn't make that account's own
    chip look unavailable."""
    if skip != "date":
        if date_from is not None:
            stmt = stmt.where(Transaction.txn_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.txn_date <= date_to)
    if skip != "account" and account_ids:
        stmt = stmt.where(Transaction.account_id.in_(account_ids))
    if skip != "category" and category_ids:
        stmt = stmt.where(Transaction.category_id.in_(category_ids))
    if exclude_category_ids:
        # Deliberately NOT gated behind `skip` — unlike category_ids
        # this isn't a filter dimension the user toggles, it's a scope
        # the caller has fixed (the Budget page's unbudgeted set), so
        # the facet counts must stay inside it. NOT IN is
        # NULL-propagating, so the explicit IS NULL keeps uncategorized
        # rows in.
        stmt = stmt.where(
            Transaction.category_id.is_(None)
            | Transaction.category_id.notin_(exclude_category_ids)
        )
    if outflows_only:
        # Money out only. Needed by the Budget page's unbudgeted
        # analysis, where the donut sums outflows (like
        # /analytics/distribution) and the record list beside it must
        # describe the same set — otherwise an income deposit shows up
        # as "unaccounted-for spend". Note the `include_excluded`
        # carve-out below always lets "Income" through, so filtering on
        # the category alone would not be enough.
        stmt = stmt.where(Transaction.amount < 0)
    if q:
        stmt = stmt.where(Transaction.description.ilike(f"%{q}%"))
    if recurring_only:
        stmt = stmt.where(Transaction.is_recurring.is_(True))
    if not include_excluded:
        stmt = stmt.where(
            func.coalesce(Category.excluded_from_analytics, False).is_(False)
            | (Category.name == "Income")
        )
    return stmt


def _transaction_to_read(txn: Transaction) -> TransactionRead:
    return TransactionRead(
        id=txn.id,
        account_id=txn.account_id,
        account_name=txn.account.display_name,
        institution_code=txn.account.institution.code,
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
        raw_row=txn.raw_row,
        created_at=txn.created_at,
    )


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List and filter transactions",
    description=(
        "Filterable, sortable, paginated transaction listing. 'Income' "
        "transactions are always included. By default (`include_excluded=false`) "
        "transactions whose category is marked `excluded_from_analytics` (e.g. "
        "'Payments & Transfers') are left out, matching the analytics endpoints' "
        "default. Pass `include_excluded=true` to include those as well."
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
            "excluded_from_analytics=true (transfers). When true, includes "
            "those too. 'Income' is always included regardless of this flag."
        ),
    ),
    exclude_category_ids: list[int] | None = Query(
        None,
        description=(
            "Category ids to omit. Uncategorized transactions are still "
            "included — used by the Budget page to list everything *not* "
            "linked to a budget expense."
        ),
    ),
    outflows_only: bool = Query(
        False,
        description=(
            "Only money out (amount < 0). Note this also drops 'Income', "
            "which `include_excluded` otherwise always lets through."
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
    stmt = _apply_filters(
        stmt,
        date_from=date_from,
        date_to=date_to,
        account_ids=account_ids,
        category_ids=category_ids,
        q=q,
        recurring_only=recurring_only,
        include_excluded=include_excluded,
        exclude_category_ids=exclude_category_ids,
        outflows_only=outflows_only,
    )

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


@router.get(
    "/facets",
    response_model=TransactionFacets,
    summary="Which account/category/month filter options currently have matching transactions",
    description=(
        "For each filter dimension (account, category, month), returns the "
        "ids/keys that have at least one matching transaction under the "
        "*other* active filters — standard faceted search, so e.g. selecting "
        "an account doesn't make that account's own chip look unavailable. "
        "The Records filter bar dims any chip missing from these lists."
    ),
)
def get_facets(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    account_ids: list[int] | None = Query(None),
    category_ids: list[int] | None = Query(None),
    q: str | None = Query(None),
    recurring_only: bool = Query(False),
    include_excluded: bool = Query(False),
    exclude_category_ids: list[int] | None = Query(
        None,
        description=(
            "Category ids to omit. Applied to every dimension (it's a fixed "
            "scope, not a toggleable filter), so facet options stay inside it."
        ),
    ),
    outflows_only: bool = Query(False, description="Only money out (amount < 0)."),
    db: Session = Depends(get_db),
) -> TransactionFacets:
    base = select(Transaction).join(Account, Transaction.account_id == Account.id)
    base = base.outerjoin(Category, Transaction.category_id == Category.id)

    def _filtered(skip: str):
        return _apply_filters(
            base,
            date_from=date_from,
            date_to=date_to,
            account_ids=account_ids,
            category_ids=category_ids,
            q=q,
            recurring_only=recurring_only,
            include_excluded=include_excluded,
            exclude_category_ids=exclude_category_ids,
            outflows_only=outflows_only,
            skip=skip,
        )

    account_stmt = _filtered("account").with_only_columns(Transaction.account_id).distinct()
    category_stmt = _filtered("category").with_only_columns(Transaction.category_id).distinct()

    month_key = func.to_char(Transaction.txn_date, "YYYY-MM")
    month_stmt = _filtered("date").with_only_columns(month_key).distinct()

    account_ids_result = [row[0] for row in db.execute(account_stmt).all()]
    category_ids_result = [row[0] for row in db.execute(category_stmt).all() if row[0] is not None]
    month_keys_result = [row[0] for row in db.execute(month_stmt).all()]

    return TransactionFacets(
        account_ids=account_ids_result,
        category_ids=category_ids_result,
        month_keys=month_keys_result,
    )


@router.post(
    "/bulk-recategorize",
    response_model=BulkRecategorizeResponse,
    summary="Recategorize many transactions at once",
    description=(
        "Sets category_id and category_source='bulk' on every given "
        "transaction id in a single statement, and records exactly one "
        "audit event for the whole operation (not one per row). 'bulk' "
        "is sticky against keyword apply_to_existing operations, same "
        "as a manual edit."
    ),
)
def bulk_recategorize(
    payload: BulkRecategorizeRequest,
    db: Session = Depends(get_db),
) -> BulkRecategorizeResponse:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {payload.category_id} not found",
        )

    result = db.execute(
        Transaction.__table__.update()
        .where(Transaction.id.in_(payload.transaction_ids))
        .values(category_id=category.id, category_source="bulk")
    )
    affected_count = result.rowcount

    record_event(
        db,
        event_type="transaction.bulk_recategorized",
        entity_type="transaction",
        entity_id=None,
        description=f"Bulk recategorized {affected_count} transaction(s) to {category.name!r}.",
        payload={"to_category": category.name, "transaction_ids": payload.transaction_ids},
        affected_count=affected_count,
    )

    db.commit()
    bump_generation()
    return BulkRecategorizeResponse(
        affected_count=affected_count, category_id=category.id, category_name=category.name
    )


@router.post(
    "/recategorize-all",
    response_model=RecategorizeAllResponse,
    summary="Re-run the current categorization rules over existing transactions",
    description=(
        "Categorization normally runs only at ingest time, so rows keep "
        "the category they got when first inserted — keywords added or "
        "re-prioritized later never reach them. This re-runs the live "
        "rules over every existing transaction and reports (or applies) "
        "the differences.\n\n"
        "Defaults to dry_run=true: nothing is written and affected_count "
        "is 0, so the blast radius can be inspected first. Manual and "
        "bulk rows are never touched. Respects the same transfer-first / "
        "priority-then-keyword-length precedence used at ingest."
    ),
)
def recategorize_all(
    payload: RecategorizeAllRequest | None = None,
    db: Session = Depends(get_db),
) -> RecategorizeAllResponse:
    request = payload or RecategorizeAllRequest()

    moves = preview_recategorize_all(db)
    candidate_count = len(moves)

    sticky_count = (
        db.execute(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.category_source.in_(["manual", "bulk"]))
        ).scalar_one()
    )

    # Resolve category names for the report before any mutation, so the
    # "from" side reflects the pre-change state.
    category_names = {
        c.id: c.name for c in db.execute(select(Category)).scalars().all()
    }
    reported = [
        RecategorizeAllMove(
            transaction_id=move.transaction.id,
            description=move.transaction.description,
            from_category_id=move.transaction.category_id,
            from_category_name=category_names.get(move.transaction.category_id),
            to_category_id=move.new_category_id,
            to_category_name=category_names.get(move.new_category_id),
            to_source=move.new_source,
        )
        for move in moves[:_MAX_REPORTED_MOVES]
    ]

    if request.dry_run:
        # Drop the uncommitted session state so a dry run can't leak the
        # loaded-and-compared rows back into the DB on a later flush.
        db.rollback()
        return RecategorizeAllResponse(
            dry_run=True,
            candidate_count=candidate_count,
            affected_count=0,
            skipped_sticky_count=sticky_count,
            moves=reported,
        )

    affected_count = apply_moves(db, moves)

    record_event(
        db,
        event_type="transaction.recategorized_all",
        entity_type="transaction",
        entity_id=None,
        description=f"Re-ran categorization rules over all transactions; {affected_count} changed.",
        payload={"candidate_count": candidate_count},
        affected_count=affected_count,
    )

    db.commit()
    bump_generation()
    return RecategorizeAllResponse(
        dry_run=False,
        candidate_count=candidate_count,
        affected_count=affected_count,
        skipped_sticky_count=sticky_count,
        moves=reported,
    )


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
        if category.id != txn.category_id:
            old_category = txn.category
            old_category_name = old_category.name if old_category is not None else None
            record_event(
                db,
                event_type="transaction.recategorized",
                entity_type="transaction",
                entity_id=txn.id,
                description=(
                    f"Recategorized transaction {txn.id} from "
                    f"{old_category_name!r} to {category.name!r}."
                ),
                payload={"from_category": old_category_name, "to_category": category.name},
                affected_count=1,
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
