"""Category and CategoryKeyword models."""
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.bucket import Bucket
    from app.models.transaction import Transaction


class Category(TimestampMixin, Base):
    """A transaction category. `priority` is ascending — lower matches first."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    excluded_from_analytics: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    bucket_id: Mapped[int] = mapped_column(
        ForeignKey("buckets.id", ondelete="RESTRICT"), nullable=False
    )
    """Coarse grouping for the category picker dropdown. Every category
    belongs to exactly one bucket; the API still serializes this as
    `group: str` (the bucket's uppercase name) for frontend compat."""

    bucket: Mapped["Bucket"] = relationship(back_populates="categories")
    keywords: Mapped[list["CategoryKeyword"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Category(id={self.id!r}, name={self.name!r}, priority={self.priority!r})"


class CategoryKeyword(Base):
    """A single keyword match rule, globally unique, belonging to one category."""

    __tablename__ = "category_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="keywords")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"CategoryKeyword(id={self.id!r}, keyword={self.keyword!r})"
