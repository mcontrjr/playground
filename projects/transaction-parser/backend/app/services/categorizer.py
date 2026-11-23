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
    matched_keyword: str | None = None
    """The keyword that actually won, for 'keyword'/'transfer' results.

    None for 'default' (nothing matched) and for 'manual'/'bulk' (a person
    chose, no rule involved). Persisted so a row can explain itself later
    without re-deriving it against rules that may since have changed.
    """


@dataclass(frozen=True, slots=True)
class _KeywordRule:
    keyword: str
    category_id: int


@dataclass(frozen=True, slots=True)
class CategoryClaim:
    """One category's claim on a description, and the keyword behind it.

    ``stage`` distinguishes *why* the claim would win or lose: a
    ``transfer`` claim is resolved before the priority scan runs at all,
    so it beats every ``keyword`` claim regardless of priority — which
    means a clash involving a transfer claim can never be fixed by
    reordering priorities.
    """

    category_id: int
    keyword: str
    stage: Literal["transfer", "keyword"]


@dataclass(frozen=True, slots=True)
class ClashReport:
    """Every category whose keywords match one description, in the order
    the categorizer would consider them (winner first).

    A clash exists when more than one *distinct* category claims the
    same description; the categorizer silently resolves it via
    transfer-first then priority, so this type is what lets the UI
    surface that decision for the user to confirm or override.
    """

    claims: list[CategoryClaim]

    @property
    def winner(self) -> CategoryClaim | None:
        return self.claims[0] if self.claims else None

    @property
    def is_clash(self) -> bool:
        return len({c.category_id for c in self.claims}) > 1

    @property
    def transfer_decided(self) -> bool:
        """True when the winner won at the transfer stage, meaning no
        priority change could alter this outcome."""
        return self.winner is not None and self.winner.stage == "transfer"


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
    def load(cls, db: Session, *, workspace_id: int) -> "Categorizer":
        """Build a ``Categorizer`` from one workspace's current
        ``categories``/``category_keywords`` rows.

        `workspace_id` is required: these rules decide what category a
        transaction gets, so loading them unscoped would let one
        workspace's keywords categorize another workspace's rows into
        categories it doesn't even own.

        Raises ``CategorizerConfigError`` if the ``Payments & Transfers``
        or ``Uncategorized`` system categories are missing from this
        workspace.
        """
        categories = db.scalars(
            select(Category).where(Category.workspace_id == workspace_id)
        ).all()
        by_name = {c.name: c for c in categories}

        transfer_category = by_name.get(TRANSFER_CATEGORY_NAME)
        if transfer_category is None:
            raise CategorizerConfigError(
                f"Required system category {TRANSFER_CATEGORY_NAME!r} is "
                "missing — has this workspace been provisioned?"
            )

        uncategorized_category = by_name.get(UNCATEGORIZED_CATEGORY_NAME)
        if uncategorized_category is None:
            raise CategorizerConfigError(
                f"Required system category {UNCATEGORIZED_CATEGORY_NAME!r} is "
                "missing — has this workspace been provisioned?"
            )

        keywords = db.scalars(
            select(CategoryKeyword).where(CategoryKeyword.workspace_id == workspace_id)
        ).all()
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
                return CategorizationResult(
                    category_id=rule.category_id,
                    source="transfer",
                    matched_keyword=rule.keyword,
                )

        for rule in self._general_rules:
            if rule.keyword in normalized_description:
                return CategorizationResult(
                    category_id=rule.category_id,
                    source="keyword",
                    matched_keyword=rule.keyword,
                )

        return CategorizationResult(
            category_id=self._uncategorized_category_id, source="default"
        )

    def explain(self, normalized_description: str) -> ClashReport:
        """Report *every* category that claims this description, in the
        same order ``categorize`` considers them — so ``claims[0]`` is
        always the category ``categorize`` actually returns.

        ``categorize`` short-circuits on the first match; this does the
        full scan instead, which is what makes a silent priority
        resolution visible. Within a category only its strongest
        (longest, earliest-considered) matching keyword is reported —
        the competing *categories* are the decision, not every keyword.
        """
        claims: list[CategoryClaim] = []
        seen: set[int] = set()

        for stage, rules in (
            ("transfer", self._transfer_rules),
            ("keyword", self._general_rules),
        ):
            for rule in rules:
                if rule.category_id in seen:
                    continue
                if rule.keyword in normalized_description:
                    claims.append(
                        CategoryClaim(
                            category_id=rule.category_id, keyword=rule.keyword, stage=stage
                        )
                    )
                    seen.add(rule.category_id)

        return ClashReport(claims=claims)
