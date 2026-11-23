"""transaction matched_keyword

Adds `transactions.matched_keyword`: the keyword that actually won when
`category_source` is 'keyword' or 'transfer'.

Previously the categorizer discarded this — it returned only the winning
category and the stage, so a row could not say *why* it landed where it
did. Recovering it after the fact means re-running the current rules,
which silently lies once a keyword has been renamed, reprioritized, or
deleted. Recording it at decision time keeps the row self-explanatory.

Null by design for:
  - 'default'          — nothing matched
  - 'manual' / 'bulk'  — a person chose; no rule was involved

The data migration backfills existing keyword/transfer rows by replaying
the *current* rules, which is exact only where the rules haven't drifted
since ingest. Rows whose replayed winner disagrees with their stored
category are left null rather than stamped with a keyword that didn't
actually decide them — a null here means "unknown", never "no match".

Revision ID: f1a2b3c4d5e6
Revises: 8e2a4c6f9b1d
Create Date: 2026-11-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "8e2a4c6f9b1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("matched_keyword", sa.String(length=128), nullable=True),
    )

    # Backfill by replaying the live rules in SQL: for each keyword/transfer
    # row, pick the matching keyword belonging to the category the row is
    # already in, preferring the longest (the categorizer's own within-
    # category tiebreak). Scoping to the stored category is what keeps a
    # drifted rule from stamping the wrong keyword — if nothing in that
    # category matches any more, the row stays null.
    op.execute(
        """
        UPDATE transactions t
        SET matched_keyword = sub.keyword
        FROM (
            SELECT DISTINCT ON (t2.id) t2.id AS txn_id, k.keyword
            FROM transactions t2
            JOIN category_keywords k ON k.category_id = t2.category_id
            WHERE t2.category_source IN ('keyword', 'transfer')
              AND position(k.keyword in t2.normalized_description) > 0
            ORDER BY t2.id, length(k.keyword) DESC
        ) AS sub
        WHERE t.id = sub.txn_id
        """
    )


def downgrade() -> None:
    op.drop_column("transactions", "matched_keyword")
