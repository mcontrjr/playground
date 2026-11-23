"""SeedSuppression: tombstones that stop the seeder resurrecting user deletes.

`app.seed` is get-or-create *by name* and runs on every backend start
(see docker-compose's backend command). An absent row is indistinguishable
from a never-seeded one, so deleting a seeded category or keyword through
the UI lasted only until the next restart. The seeded rows came back, and
with them the keywords that had been deliberately removed.

A tombstone records the user's intent to *not have* a seeded item, which
has to outlive the row itself — deletes here are hard deletes (categories
cascade their keywords), so there is no row left to carry a `deleted_at`
flag. Keying on the natural key (name / keyword text) rather than the id
is deliberate: the seeder matches on that same natural key, and the id of
a deleted row is gone for good.

`kind` distinguishes the two namespaces a name can live in; a category
called "GAS" and a keyword "GAS" are unrelated suppressions.
"""
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SeedSuppression(Base):
    """One seeded item the user removed and the seeder must not recreate."""

    __tablename__ = "seed_suppressions"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "kind", "name", name="uq_seed_suppressions_kind_name"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    """One workspace deleting a seeded category must not suppress it for
    everyone else."""
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    """Either 'category' or 'keyword' — the namespace `name` belongs to."""

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    """The natural key the seeder matches on: category name or keyword text.
    Keywords are stored upper-cased, matching the seeder's normalization."""

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"SeedSuppression(kind={self.kind!r}, name={self.name!r})"


CATEGORY = "category"
KEYWORD = "keyword"
