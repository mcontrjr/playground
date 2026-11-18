"""bulk category source and fixed expenses

Two independent additions, bundled since both are small:

1. Widens the `ck_transactions_category_source` check constraint to
   allow `'bulk'` alongside the existing `keyword`/`manual`/`transfer`/
   `default` values — set by the new bulk-recategorize endpoint so
   those rows are distinguishable from a single manual edit while
   still being sticky against keyword `apply_to_existing` operations
   (the stickiness check only tests for `category_source == 'keyword'`
   it's moving FROM, not the source value itself).
2. Adds `budget_expenses.is_fixed` (default false) — a fixed monthly
   expense (e.g. rent) has a known recurring amount rather than a goal
   to hit, so the API will force `goal_amount` to null whenever this
   flag is true.

Revision ID: 8e2a4c6f9b1d
Revises: 5ba8bd95cf01
Create Date: 2026-11-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e2a4c6f9b1d"
down_revision: Union[str, None] = "5ba8bd95cf01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_transactions_category_source", "transactions", type_="check")
    op.create_check_constraint(
        "ck_transactions_category_source",
        "transactions",
        "category_source IN ('keyword', 'manual', 'transfer', 'default', 'bulk')",
    )

    op.add_column(
        "budget_expenses",
        sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("budget_expenses", "is_fixed")

    op.drop_constraint("ck_transactions_category_source", "transactions", type_="check")
    op.create_check_constraint(
        "ck_transactions_category_source",
        "transactions",
        "category_source IN ('keyword', 'manual', 'transfer', 'default')",
    )
