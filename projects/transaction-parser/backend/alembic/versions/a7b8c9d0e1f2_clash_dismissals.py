"""clash dismissals

Adds `clash_dismissals`: conflicts the user reviewed and judged correct
as-is, so the Conflicts queue stops showing them.

Two shapes in one table, distinguished by `transaction_id`:
  - null  -> rule-level: "when these two categories compete and this one
             wins, that's right" — suppresses current *and future* rows
             of that shape, including ones created by a re-import.
  - set   -> row-level: this one record is fine, pairing not judged.

Not the same as resolving a clash: resolving writes
`category_source='manual'`, pinning the row against all future rule
changes. A dismissal records a judgment about the *rules* and leaves the
transaction untouched, so a later keyword fix still reaches it.

Postgres treats NULLs as distinct in unique constraints, so the table
constraint alone would allow duplicate rule-level rows for the same
pairing. Two partial unique indexes enforce it properly instead: one for
rule-level rows (transaction_id IS NULL), one for row-level rows.

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clash_dismissals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("winner_category_id", sa.Integer(), nullable=False),
        sa.Column("loser_category_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["winner_category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["loser_category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Rule-level: one dismissal per (winner, loser) pairing.
    op.create_index(
        "uq_clash_dismissal_rule",
        "clash_dismissals",
        ["winner_category_id", "loser_category_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NULL"),
    )
    # Row-level: one dismissal per (winner, loser, transaction).
    op.create_index(
        "uq_clash_dismissal_row",
        "clash_dismissals",
        ["winner_category_id", "loser_category_id", "transaction_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NOT NULL"),
    )
    op.create_index(
        "ix_clash_dismissals_transaction_id", "clash_dismissals", ["transaction_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_clash_dismissals_transaction_id", table_name="clash_dismissals")
    op.drop_index("uq_clash_dismissal_row", table_name="clash_dismissals")
    op.drop_index("uq_clash_dismissal_rule", table_name="clash_dismissals")
    op.drop_table("clash_dismissals")
