"""budget expenses

Adds `budget_expenses` (user-defined monthly budget line items, e.g.
Rent, Groceries — not month-scoped themselves, reusable across months)
and `budget_expense_categories` (many-to-many link to `categories`, used
to auto-total a budget expense's "actual" spend for a given month from
its linked categories' transactions).

Revision ID: 5ba8bd95cf01
Revises: d4f7a1c3e5b9
Create Date: 2026-11-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ba8bd95cf01"
down_revision: Union[str, None] = "d4f7a1c3e5b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budget_expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("goal_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "budget_expense_categories",
        sa.Column("budget_expense_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["budget_expense_id"], ["budget_expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("budget_expense_id", "category_id"),
    )


def downgrade() -> None:
    op.drop_table("budget_expense_categories")
    op.drop_table("budget_expenses")
