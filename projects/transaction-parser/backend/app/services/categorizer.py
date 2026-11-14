"""Categorization engine.

Loads categories and keywords from the database once per ingest batch
(``Categorizer.load`` performs the queries; ``categorize`` is then a
pure in-memory lookup per transaction), and applies the three-stage
rule from the plan:

1. Transfer check: keywords belonging to the system category named
   ``Payments & Transfers`` are matched first, regardless of priority.
   This is what catches both the card-side credit (e.g. Amex "AUTOPAY
   PAYMENT - THANK YOU") and the checking-side debit (e.g. Schwab
   "CITI CARD ONLINE PAYMENT") of the same real-world transfer.
2. General keyword scan: every other category's keywords, ordered by
   ``category.priority`` ascending, then keyword length descending
   (so a longer, more specific keyword wins over a short substring of
   it when both belong to the same category pass). First substring
   match against ``normalized_description`` wins.
3. Fallback: the system ``Uncategorized`` category.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, CategoryKeyword

CategorySource = Literal["keyword", "manual", "transfer", "default"]

TRANSFER_CATEGORY_NAME = "Payments & Transfers"
UNCATEGORIZED_CATEGORY_NAME = "Uncategorized"


class CategorizerConfigError(RuntimeError):
    """Raised when a required system category is missing from the DB.

    This should only happen if the seed script hasn't been run against
    the target database.
    """


@dataclass(frozen=True, slots=True)
class CategorizationResult:
    """The outcome of categorizing a single normalized description."""

    category_id: int
    source: CategorySource


@dataclass(frozen=True, slots=True)
class _KeywordRule:
    keyword: str
    category_id: int


class Categorizer:
    """Loads category/keyword state once, then categorizes many rows.

    Construct via :meth:`load` at the start of an ingest batch so every
    row in the batch is categorized against one consistent snapshot of
    the category/keyword tables.
    """

    def __init__(
        self,
        transfer_rules: list[_KeywordRule],
        general_rules: list[_KeywordRule],
        uncategorized_category_id: int,
    ) -> None:
        self._transfer_rules = transfer_rules
        self._general_rules = general_rules
        self._uncategorized_category_id = uncategorized_category_id

    @classmethod
    def load(cls, db: Session) -> "Categorizer":
        """Build a ``Categorizer`` from the current state of the
        ``categories``/``category_keywords`` tables.

        Raises ``CategorizerConfigError`` if the ``Payments & Transfers``
        or ``Uncategorized`` system categories haven't been seeded.
        """
        categories = db.execute(select(Category)).scalars().all()
        by_name = {c.name: c for c in categories}

        transfer_category = by_name.get(TRANSFER_CATEGORY_NAME)
        if transfer_category is None:
            raise CategorizerConfigError(
                f"Required system category {TRANSFER_CATEGORY_NAME!r} is "
                "missing — has the seed script been run?"
            )

        uncategorized_category = by_name.get(UNCATEGORIZED_CATEGORY_NAME)
        if uncategorized_category is None:
            raise CategorizerConfigError(
                f"Required system category {UNCATEGORIZED_CATEGORY_NAME!r} is "
                "missing — has the seed script been run?"
            )

        keywords = db.execute(select(CategoryKeyword)).scalars().all()
        keywords_by_category_id: dict[int, list[str]] = {}
        for kw in keywords:
            keywords_by_category_id.setdefault(kw.category_id, []).append(kw.keyword)

        transfer_rules = [
            _KeywordRule(keyword=kw, category_id=transfer_category.id)
            for kw in sorted(
                keywords_by_category_id.get(transfer_category.id, []),
                key=len,
                reverse=True,
            )
        ]

        # General scan: every other category, ordered by priority ASC,
        # then keyword length DESC within each category.
        other_categories = sorted(
            (c for c in categories if c.id != transfer_category.id),
            key=lambda c: c.priority,
        )
        general_rules: list[_KeywordRule] = []
        for category in other_categories:
            for kw in sorted(
                keywords_by_category_id.get(category.id, []),
                key=len,
                reverse=True,
            ):
                general_rules.append(_KeywordRule(keyword=kw, category_id=category.id))

        return cls(
            transfer_rules=transfer_rules,
            general_rules=general_rules,
            uncategorized_category_id=uncategorized_category.id,
        )

    def categorize(self, normalized_description: str) -> CategorizationResult:
        """Categorize one already-normalized (upper, whitespace-collapsed)
        description string."""
        for rule in self._transfer_rules:
            if rule.keyword in normalized_description:
                return CategorizationResult(category_id=rule.category_id, source="transfer")

        for rule in self._general_rules:
            if rule.keyword in normalized_description:
                return CategorizationResult(category_id=rule.category_id, source="keyword")

        return CategorizationResult(
            category_id=self._uncategorized_category_id, source="default"
        )
