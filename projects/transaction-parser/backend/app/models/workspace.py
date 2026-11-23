"""Workspace model: the tenant every piece of user configuration hangs off.

The app began life single-user, with one implicit set of accounts,
categories, buckets, keywords and budget lines. A workspace makes that
set explicit and repeatable: `slug` is a username-like public handle
(what you type on the splash screen to get back in), `name` is the
display label.

There is deliberately no auth here — knowing the slug is enough to enter
a workspace. That keeps the door open for real accounts later (a
`users` table referencing workspaces) without reshaping the data model
now.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.bucket import Bucket
    from app.models.category import Category


class Workspace(TimestampMixin, Base):
    """One user's isolated set of records and configuration."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    """Lowercased handle, unique across the install. Validated and
    normalized at the API layer (see `app.api.workspaces`)."""

    name: Mapped[str] = mapped_column(String(80), nullable=False)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    buckets: Mapped[list["Bucket"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Workspace(id={self.id!r}, slug={self.slug!r})"
