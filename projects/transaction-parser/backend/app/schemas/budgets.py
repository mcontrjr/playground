"""Pydantic v2 schemas for the Budget tab."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCategoryRef(BaseModel):
    """A category linked to a budget expense, for display."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class BudgetExpenseRead(BaseModel):
    """A budget expense with its linked categories and, when a month is
    given to the listing endpoint, that month's computed actual spend."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Groceries",
                    "goal_amount": "600.00",
                    "sort_order": 0,
                    "categories": [{"id": 11, "name": "Groceries"}],
                    "actual_amount": "482.19",
                }
            ]
        }
    )

    id: int
    name: str
    goal_amount: Decimal | None = Field(description="Manually-entered monthly target; null if none set.")
    sort_order: int
    categories: list[BudgetCategoryRef] = Field(description="Transaction categories linked to this expense.")
    actual_amount: Decimal = Field(
        description="Sum of outflows (as a positive number) across the linked categories for the requested month. 0 if no categories are linked or none match."
    )


class BudgetExpenseCreate(BaseModel):
    """Request body to create a budget expense."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Groceries", "goal_amount": "600.00", "category_ids": [11]}]}
    )

    name: str = Field(min_length=1, max_length=128)
    goal_amount: Decimal | None = None
    category_ids: list[int] = Field(default_factory=list)


class BudgetExpenseUpdate(BaseModel):
    """Request body to edit a budget expense. Only provided fields change.
    `category_ids`, when provided, REPLACES the full set of linked
    categories (not a merge)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"goal_amount": "650.00"}]})

    name: str | None = Field(default=None, min_length=1, max_length=128)
    goal_amount: Decimal | None = None
    category_ids: list[int] | None = None
    sort_order: int | None = None


class BudgetExpenseDeleteResult(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"deleted_budget_expense_id": 1}]})

    deleted_budget_expense_id: int


class BudgetSummary(BaseModel):
    """The Budget tab's month-scoped overview: auto-imported income plus
    every expense's actual-vs-goal for that same month."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "month": "2026-11",
                    "income": "6200.00",
                    "total_goal": "3200.00",
                    "total_actual": "2940.55",
                    "expenses": [
                        {
                            "id": 1,
                            "name": "Groceries",
                            "goal_amount": "600.00",
                            "sort_order": 0,
                            "categories": [{"id": 11, "name": "Groceries"}],
                            "actual_amount": "482.19",
                        }
                    ],
                }
            ]
        }
    )

    month: str = Field(description="YYYY-MM")
    income: Decimal = Field(description="Sum of the 'Income' category's transactions this month, as a positive number.")
    total_goal: Decimal = Field(description="Sum of every expense's goal_amount that has one set.")
    total_actual: Decimal = Field(description="Sum of every expense's actual_amount.")
    expenses: list[BudgetExpenseRead]
