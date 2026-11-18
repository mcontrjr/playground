"""Bucket model: a coarse grouping for categories.

Bucket names are always stored stripped + uppercase (enforced at the API
layer). ``OTHER`` is the undeletable, unrenamable fallback bucket every
category lands in by default.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category


class Bucket(TimestampMixin, Base):
    """A coarse category grouping (e.g. ESSENTIALS, LIFESTYLE, OTHER)."""

    __tablename__ = "buckets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    categories: Mapped[list["Category"]] = relationship(back_populates="bucket")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Bucket(id={self.id!r}, name={self.name!r})"
