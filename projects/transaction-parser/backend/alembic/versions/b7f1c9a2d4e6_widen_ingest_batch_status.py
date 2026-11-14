"""widen ingest_batches status check constraint

Adds `completed_with_errors` as a valid status, per the Phase 3 ingest
pipeline: a batch with zero parse failures is `completed`, a batch with
one or more isolated row failures is `completed_with_errors` (the
upload still succeeds — it's not a 500 — but the response/UI should
show it as a partial outcome), and a batch that aborted via a DB/
exception path is `failed`.

Revision ID: b7f1c9a2d4e6
Revises: 7a6d0cd0a1f3
Create Date: 2026-11-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7f1c9a2d4e6"
down_revision: Union[str, None] = "7a6d0cd0a1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_ingest_batches_status", "ingest_batches", type_="check"
    )
    # Widen from VARCHAR(16) so 'completed_with_errors' (21 chars) fits.
    op.alter_column(
        "ingest_batches",
        "status",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
        existing_server_default="pending",
    )
    op.create_check_constraint(
        "ck_ingest_batches_status",
        "ingest_batches",
        "status IN ('pending', 'completed', 'completed_with_errors', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_ingest_batches_status", "ingest_batches", type_="check"
    )
    op.alter_column(
        "ingest_batches",
        "status",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=False,
        existing_server_default="pending",
    )
    op.create_check_constraint(
        "ck_ingest_batches_status",
        "ingest_batches",
        "status IN ('pending', 'completed', 'failed')",
    )
