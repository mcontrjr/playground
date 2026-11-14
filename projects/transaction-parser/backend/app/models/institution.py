"""Institution model: the 5 supported banks/card issuers."""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account


class Institution(TimestampMixin, Base):
    """A bank or card issuer whose CSV export format we know how to parse."""

    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Institution(id={self.id!r}, code={self.code!r})"
