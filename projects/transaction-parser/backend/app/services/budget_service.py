"""Budget aggregation: computes each BudgetExpense's actual spend for a
given month from its linked categories' transactions, and the month's
auto-imported income total. Nothing here is stored — every number is
derived live from `transactions` so it always reflects current
categorization, same philosophy as the analytics endpoints.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BudgetExpense, Transaction, budget_expense_categories


def month_bounds(month: date) -> tuple[date, date]:
    days_in_month = calendar.monthrange(month.year, month.month)[1]
    return date(month.year, month.month, 1), date(month.year, month.month, days_in_month)


@dataclass(frozen=True, slots=True)
class ExpenseActuals:
    """budget_expense_id -> this month's actual spend (positive Decimal)."""

    by_expense_id: dict[int, Decimal]


def compute_actuals(db: Session, month: date, expense_ids: list[int] | None = None) -> ExpenseActuals:
    """Sum of outflows (amount < 0, reported as a positive number) per
    budget expense, across that expense's linked categories, for the
    given month. An expense with no linked categories (or none of its
    categories had any matching transactions) is simply absent from the
    result — callers default to Decimal('0.00')."""
    month_start, month_end = month_bounds(month)

    stmt = (
        select(
            budget_expense_categories.c.budget_expense_id,
            func.coalesce(func.sum(-Transaction.amount), 0).label("actual"),
        )
        .select_from(budget_expense_categories)
        .join(Transaction, Transaction.category_id == budget_expense_categories.c.category_id)
        .where(Transaction.txn_date >= month_start)
        .where(Transaction.txn_date <= month_end)
        .where(Transaction.amount < 0)
        .group_by(budget_expense_categories.c.budget_expense_id)
    )
    if expense_ids is not None:
        stmt = stmt.where(budget_expense_categories.c.budget_expense_id.in_(expense_ids))

    rows = db.execute(stmt).all()
    return ExpenseActuals(
        by_expense_id={r.budget_expense_id: Decimal(r.actual).quantize(Decimal("0.01")) for r in rows}
    )


def actual_for_expense(expense: BudgetExpense, actuals: ExpenseActuals) -> Decimal:
    return actuals.by_expense_id.get(expense.id, Decimal("0.00"))
