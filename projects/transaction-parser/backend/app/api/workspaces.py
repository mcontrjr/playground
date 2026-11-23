"""Workspace lifecycle: enter an existing one, create a new one, load it.

This is the only router that does *not* depend on `get_workspace` — it is
what the splash screen talks to before a workspace is chosen, so it
takes the slug in the path instead of the header.

`GET /workspaces/{slug}/bootstrap` exists so entering a workspace is one
request rather than six. The splash screen's spinning logo is up for
exactly that one round trip, and the client can prime its React Query
caches before the first page renders.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.accounts import _account_rows_to_read
from app.api.buckets import _bucket_to_read
from app.api.budgets import _expense_to_read
from app.api.categories import _category_to_read
from app.db import get_db
from app.models import (
    Account,
    Bucket,
    BudgetExpense,
    Category,
    Institution,
    Transaction,
    Workspace,
)
from app.provisioning import provision_workspace
from app.schemas.workspaces import (
    SLUG_PATTERN,
    SLUG_RULES,
    SlugAvailability,
    WorkspaceBootstrap,
    WorkspaceCreate,
    WorkspaceRead,
    normalize_slug,
)
from app.services.budget_service import ExpenseActuals

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _get_or_404(db: Session, slug: str) -> Workspace:
    workspace = db.scalar(
        select(Workspace).where(Workspace.slug == normalize_slug(slug))
    )
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WORKSPACE_NOT_FOUND",
                "message": f"No workspace named {slug!r}.",
            },
        )
    return workspace


@router.get(
    "/{slug}/availability",
    response_model=SlugAvailability,
    summary="Check whether a workspace name is free",
    description=(
        "Powers the create form's live uniqueness check. Reports malformed "
        "names as unavailable with a reason, so the form has one code path "
        "for both kinds of rejection."
    ),
)
def check_availability(slug: str, db: Session = Depends(get_db)) -> SlugAvailability:
    normalized = normalize_slug(slug)

    if not SLUG_PATTERN.match(normalized):
        return SlugAvailability(
            slug=normalized, available=False, reason=f"Invalid name. {SLUG_RULES}"
        )

    taken = db.scalar(
        select(func.count()).select_from(Workspace).where(Workspace.slug == normalized)
    )
    if taken:
        return SlugAvailability(
            slug=normalized,
            available=False,
            reason="That workspace name is already taken.",
        )
    return SlugAvailability(slug=normalized, available=True, reason=None)


@router.get(
    "/{slug}",
    response_model=WorkspaceRead,
    summary="Resolve a workspace by name",
    description="404s when the name is unknown. Used to validate the splash screen's 'enter existing' form before loading.",
)
def get_workspace_by_slug(slug: str, db: Session = Depends(get_db)) -> WorkspaceRead:
    return WorkspaceRead.model_validate(_get_or_404(db, slug))


@router.post(
    "",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
    description=(
        "Creates the workspace and provisions its default buckets, "
        "categories and keywords (see `app.provisioning`). No budget lines "
        "are created — the Budget page starts empty so the user sets their "
        "own targets. 409 when the name is taken."
    ),
)
def create_workspace(
    payload: WorkspaceCreate, db: Session = Depends(get_db)
) -> WorkspaceRead:
    # The slug is already normalized + format-checked by the schema's
    # validator; this is the uniqueness check, which needs the database.
    existing = db.scalar(select(Workspace).where(Workspace.slug == payload.slug))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "WORKSPACE_TAKEN",
                "message": f"Workspace {payload.slug!r} already exists.",
            },
        )

    workspace = Workspace(slug=payload.slug, name=payload.name or payload.slug)
    db.add(workspace)
    db.flush()

    provision_workspace(db, workspace)
    db.commit()
    db.refresh(workspace)

    return WorkspaceRead.model_validate(workspace)


@router.get(
    "/{slug}/bootstrap",
    response_model=WorkspaceBootstrap,
    summary="Load a whole workspace in one request",
    description=(
        "Returns the workspace plus its accounts, buckets, categories "
        "(with keywords) and budget lines, and whether it has any "
        "transactions yet. `has_transactions` is what gates the data pages "
        "in the sidebar."
    ),
)
def bootstrap_workspace(slug: str, db: Session = Depends(get_db)) -> WorkspaceBootstrap:
    workspace = _get_or_404(db, slug)
    ws_id = workspace.id

    transaction_count = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.workspace_id == ws_id)
    ) or 0

    # --- accounts (same shape as GET /accounts) ----------------------------
    account_rows = db.execute(
        select(
            Account,
            Institution.code.label("institution_code"),
            Institution.display_name.label("institution_name"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Institution, Account.institution_id == Institution.id)
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .where(Account.workspace_id == ws_id)
        .group_by(Account.id, Institution.code, Institution.display_name)
        .order_by(Institution.display_name, Account.display_name)
    ).all()

    # --- buckets (same shape as GET /buckets) ------------------------------
    buckets = db.scalars(
        select(Bucket).where(Bucket.workspace_id == ws_id).order_by(Bucket.name)
    ).all()
    bucket_counts = dict(
        db.execute(
            select(Category.bucket_id, func.count())
            .where(Category.workspace_id == ws_id)
            .group_by(Category.bucket_id)
        ).all()
    )

    # --- categories (same shape as GET /categories) ------------------------
    categories = db.scalars(
        select(Category)
        .where(Category.workspace_id == ws_id)
        .order_by(Category.priority)
    ).all()
    category_counts = dict(
        db.execute(
            select(Transaction.category_id, func.count())
            .where(Transaction.workspace_id == ws_id)
            .group_by(Transaction.category_id)
        ).all()
    )

    # --- budget lines, month-less -----------------------------------------
    # `actual_amount` needs a month to mean anything; the Budget page
    # fetches its own month-scoped summary, so an empty actuals map here
    # yields 0 for every line rather than a misleading number.
    expenses = db.scalars(
        select(BudgetExpense)
        .where(BudgetExpense.workspace_id == ws_id)
        .options(selectinload(BudgetExpense.categories))
        .order_by(BudgetExpense.sort_order, BudgetExpense.id)
    ).all()
    no_actuals = ExpenseActuals(by_expense_id={})

    return WorkspaceBootstrap(
        workspace=WorkspaceRead.model_validate(workspace),
        has_transactions=transaction_count > 0,
        transaction_count=transaction_count,
        accounts=_account_rows_to_read(account_rows),
        buckets=[_bucket_to_read(b, bucket_counts.get(b.id, 0)) for b in buckets],
        categories=[
            _category_to_read(c, category_counts.get(c.id, 0)) for c in categories
        ],
        budget_expenses=[_expense_to_read(e, no_actuals) for e in expenses],
    )
