"""recurrence flag, category groups, and a user_preferences cache table

Three independent additions for the parser-2.0 UI rework:

- `transactions.is_recurring` / `transactions.recurrence` ('monthly' |
  'yearly') let a transaction be flagged as a recurring bill/subscription
  independent of its category, surfaced site-wide.
- `categories.group` is a coarse label (Essentials/Lifestyle/Income/
  Transfers/Savings/...) so the Records category dropdown can group
  options by type instead of a flat alphabetical list.
- `user_preferences` is a tiny opaque key->JSON cache so the frontend can
  persist the active theme and each page's last-used filters server-side
  instead of re-deriving or losing them on reload.

Revision ID: c3d8e5f1a9b2
Revises: b7f1c9a2d4e6
Create Date: 2026-11-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d8e5f1a9b2"
down_revision: Union[str, None] = "b7f1c9a2d4e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("is_recurring", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "transactions",
        sa.Column("recurrence", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_transactions_recurrence",
        "transactions",
        "recurrence IS NULL OR recurrence IN ('monthly', 'yearly')",
    )

    op.add_column(
        "categories",
        sa.Column("group", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "user_preferences",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_column("categories", "group")
    op.drop_constraint("ck_transactions_recurrence", "transactions", type_="check")
    op.drop_column("transactions", "recurrence")
    op.drop_column("transactions", "is_recurring")
