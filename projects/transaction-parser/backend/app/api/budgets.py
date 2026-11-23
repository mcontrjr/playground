"""Budget tab: CRUD for user-defined budget expenses plus the
month-scoped summary (auto-imported income + each expense's
actual-vs-goal), computed live from transactions."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import get_workspace
from app.models import BudgetExpense, Category, Workspace
from app.schemas.budgets import (
    BudgetCategoryRef,
    BudgetExpenseCreate,
    BudgetExpenseDeleteResult,
    BudgetExpenseRead,
    BudgetExpenseUpdate,
    BudgetSummary,
)
from app.services.audit_service import record_event
from app.services.budget_service import ExpenseActuals, actual_for_expense, compute_actuals
from app.services.cache import bump_generation

router = APIRouter(prefix="/budget", tags=["budget"])


def _expense_to_read(expense: BudgetExpense, actuals: ExpenseActuals) -> BudgetExpenseRead:
    return BudgetExpenseRead(
        id=expense.id,
        name=expense.name,
        goal_amount=expense.goal_amount,
        is_fixed=expense.is_fixed,
        sort_order=expense.sort_order,
        categories=[BudgetCategoryRef(id=c.id, name=c.name) for c in expense.categories],
        actual_amount=actual_for_expense(expense, actuals),
    )


def _resolve_categories(
    db: Session, workspace_id: int, category_ids: list[int]
) -> list[Category]:
    if not category_ids:
        return []
    # Scoped so a budget line can never link a category from another
    # workspace: such an id falls into `missing` and 404s.
    categories = db.execute(
        select(Category).where(
            Category.workspace_id == workspace_id, Category.id.in_(category_ids)
        )
    ).scalars().all()
    found_ids = {c.id for c in categories}
    missing = set(category_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categories not found: {sorted(missing)}",
        )
    return list(categories)


def _parse_month(month: str) -> date:
    try:
        year_str, month_str = month.split("-")
        return date(int(year_str), int(month_str), 1)
    except (ValueError, IndexError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid month {month!r}; expected YYYY-MM.",
        ) from exc


@router.get(
    "/summary",
    response_model=BudgetSummary,
    summary="Month-scoped budget overview",
    description=(
        "Auto-imported income (sum of the 'Income' category's transactions "
        "this month) plus every budget expense with that month's computed "
        "actual spend against its goal."
    ),
)
def get_summary(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BudgetSummary:
    month_date = _parse_month(month)
    expenses = (
        db.execute(
            select(BudgetExpense)
            .where(BudgetExpense.workspace_id == ws.id)
            .options(selectinload(BudgetExpense.categories))
            .order_by(BudgetExpense.sort_order, BudgetExpense.name)
        )
        .scalars()
        .all()
    )
    actuals = compute_actuals(db, ws.id, month_date)

    expense_reads = [_expense_to_read(e, actuals) for e in expenses]
    total_goal = sum((e.goal_amount for e in expense_reads if e.goal_amount is not None), Decimal("0.00"))
    total_actual = sum((e.actual_amount for e in expense_reads), Decimal("0.00"))
    total_fixed = sum((e.actual_amount for e in expense_reads if e.is_fixed), Decimal("0.00"))

    return BudgetSummary(
        month=month,
        total_goal=total_goal,
        total_actual=total_actual,
        total_fixed=total_fixed,
        expenses=expense_reads,
    )


@router.post(
    "",
    response_model=BudgetExpenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budget expense",
)
def create_expense(
    payload: BudgetExpenseCreate,
    month: str = Query(..., description="YYYY-MM — which month's actual_amount to return in the response."),
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BudgetExpenseRead:
    categories = _resolve_categories(db, ws.id, payload.category_ids)

    max_sort_order = db.execute(
        select(BudgetExpense.sort_order)
        .where(BudgetExpense.workspace_id == ws.id)
        .order_by(BudgetExpense.sort_order.desc())
    ).scalars().first()
    expense = BudgetExpense(
        workspace_id=ws.id,
        name=payload.name,
        goal_amount=None if payload.is_fixed else payload.goal_amount,
        is_fixed=payload.is_fixed,
        sort_order=(max_sort_order or 0) + 1,
        categories=categories,
    )
    db.add(expense)
    db.flush()

    record_event(
        db,
        workspace_id=ws.id,
        event_type="budget_expense.created",
        entity_type="budget_expense",
        entity_id=expense.id,
        description=f"Created budget expense {expense.name!r}.",
        payload={"name": expense.name, "category_ids": [c.id for c in categories]},
    )

    db.commit()
    db.refresh(expense)
    bump_generation()

    month_date = _parse_month(month)
    actuals = compute_actuals(db, ws.id, month_date, expense_ids=[expense.id])
    return _expense_to_read(expense, actuals)


@router.patch(
    "/{expense_id}",
    response_model=BudgetExpenseRead,
    summary="Edit a budget expense",
    description="Only provided fields change. `category_ids`, when given, REPLACES the linked set.",
)
def patch_expense(
    expense_id: int,
    payload: BudgetExpenseUpdate,
    month: str = Query(..., description="YYYY-MM — which month's actual_amount to return in the response."),
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BudgetExpenseRead:
    expense = db.get(BudgetExpense, expense_id)
    if expense is None or expense.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget expense not found")

    fields_set = payload.model_fields_set
    if payload.name is not None:
        expense.name = payload.name
    if payload.is_fixed is not None:
        expense.is_fixed = payload.is_fixed
    if "goal_amount" in fields_set:
        expense.goal_amount = payload.goal_amount
    if expense.is_fixed:
        expense.goal_amount = None
    if payload.sort_order is not None:
        expense.sort_order = payload.sort_order
    if payload.category_ids is not None:
        expense.categories = _resolve_categories(db, ws.id, payload.category_ids)

    record_event(
        db,
        workspace_id=ws.id,
        event_type="budget_expense.updated",
        entity_type="budget_expense",
        entity_id=expense.id,
        description=f"Updated budget expense {expense.name!r}.",
        payload={"name": expense.name},
    )

    db.commit()
    db.refresh(expense)
    bump_generation()

    month_date = _parse_month(month)
    actuals = compute_actuals(db, ws.id, month_date, expense_ids=[expense.id])
    return _expense_to_read(expense, actuals)


@router.delete(
    "/{expense_id}",
    response_model=BudgetExpenseDeleteResult,
    summary="Delete a budget expense",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    ws: Workspace = Depends(get_workspace),
) -> BudgetExpenseDeleteResult:
    expense = db.get(BudgetExpense, expense_id)
    if expense is None or expense.workspace_id != ws.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget expense not found")

    deleted_name = expense.name
    db.delete(expense)

    record_event(
        db,
        workspace_id=ws.id,
        event_type="budget_expense.deleted",
        entity_type="budget_expense",
        entity_id=expense_id,
        description=f"Deleted budget expense {deleted_name!r}.",
        payload={"name": deleted_name},
    )

    db.commit()
    bump_generation()

    return BudgetExpenseDeleteResult(deleted_budget_expense_id=expense_id)
