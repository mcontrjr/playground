"""UserPreference: a tiny server-side cache of UI state.

This app is single-user/local, so there's no auth model to key
preferences off of — one row per `key` (e.g. "theme", "filters:records",
"filters:time-series") is sufficient. Values are opaque JSON blobs the
frontend defines and reads back verbatim; the backend never interprets
them, it just persists and serves the last value written, which is the
"cache users' previous filters across pages" behavior the UI wants
without re-deriving anything client-side on reload.
"""
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class UserPreference(TimestampMixin, Base):
    """One opaque, key-addressed JSON blob of persisted UI state."""

    __tablename__ = "user_preferences"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"UserPreference(key={self.key!r})"
