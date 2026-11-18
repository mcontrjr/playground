"""BudgetExpense model: a user-defined monthly budget line item.

A BudgetExpense (e.g. "Groceries", "Rent") optionally links one or more
Categories via `budget_expense_categories`; its "actual" spend for a
given month is computed on read as the sum of transactions in those
categories for that month (never stored), so it always reflects the
current categorization. `goal_amount` is a manually-entered target,
independent of the linked categories' sum.
"""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category


budget_expense_categories = Table(
    "budget_expense_categories",
    Base.metadata,
    Column("budget_expense_id", Integer, ForeignKey("budget_expenses.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class BudgetExpense(TimestampMixin, Base):
    """A user-defined budget line (e.g. Rent, Groceries), reusable across
    months. Not month-scoped itself — the month only affects which
    transactions get summed for its linked categories."""

    __tablename__ = "budget_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    goal_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")

    categories: Mapped[list["Category"]] = relationship(
        secondary=budget_expense_categories,
        order_by="Category.name",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"BudgetExpense(id={self.id!r}, name={self.name!r})"
