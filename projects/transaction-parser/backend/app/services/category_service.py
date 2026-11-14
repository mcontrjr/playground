"""Category management service: CRUD side-effects, keyword management,
and the keyword impact-preview dry-run.

The impact-preview logic reuses ``Categorizer`` itself rather than
approximating keyword precedence: to answer "what would description X
get if keyword K were added to/removed from category C", we build a
second ``Categorizer`` snapshot with the hypothetical keyword set and
re-run ``categorize()`` against every candidate transaction's
``normalized_description``. This guarantees the preview (and the
subsequent apply) respects the exact same transfer-first /
priority-then-length keyword precedence used at ingest time.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, CategoryKeyword, Transaction
from app.services.categorizer import (
    TRANSFER_CATEGORY_NAME,
    UNCATEGORIZED_CATEGORY_NAME,
    Categorizer,
    CategorizerConfigError,
    _KeywordRule,
)


@dataclass(frozen=True, slots=True)
class _CategorySnapshot:
    categories: list[Category]
    keywords_by_category_id: dict[int, list[str]]


def _load_snapshot(db: Session) -> _CategorySnapshot:
    categories = list(db.execute(select(Category)).scalars().all())
    keywords = list(db.execute(select(CategoryKeyword)).scalars().all())
    keywords_by_category_id: dict[int, list[str]] = {}
    for kw in keywords:
        keywords_by_category_id.setdefault(kw.category_id, []).append(kw.keyword)
    return _CategorySnapshot(categories=categories, keywords_by_category_id=keywords_by_category_id)


def _build_categorizer_from_snapshot(snapshot: _CategorySnapshot) -> Categorizer:
    """Mirror of ``Categorizer.load`` but operating on an in-memory
    snapshot that may have been hypothetically mutated, instead of
    querying the DB directly."""
    by_name = {c.name: c for c in snapshot.categories}

    transfer_category = by_name.get(TRANSFER_CATEGORY_NAME)
    if transfer_category is None:
        raise CategorizerConfigError(
            f"Required system category {TRANSFER_CATEGORY_NAME!r} is missing"
        )
    uncategorized_category = by_name.get(UNCATEGORIZED_CATEGORY_NAME)
    if uncategorized_category is None:
        raise CategorizerConfigError(
            f"Required system category {UNCATEGORIZED_CATEGORY_NAME!r} is missing"
        )

    transfer_rules = [
        _KeywordRule(keyword=kw, category_id=transfer_category.id)
        for kw in sorted(
            snapshot.keywords_by_category_id.get(transfer_category.id, []),
            key=len,
            reverse=True,
        )
    ]

    other_categories = sorted(
        (c for c in snapshot.categories if c.id != transfer_category.id),
        key=lambda c: c.priority,
    )
    general_rules: list[_KeywordRule] = []
    for category in other_categories:
        for kw in sorted(
            snapshot.keywords_by_category_id.get(category.id, []),
            key=len,
            reverse=True,
        ):
            general_rules.append(_KeywordRule(keyword=kw, category_id=category.id))

    return Categorizer(
        transfer_rules=transfer_rules,
        general_rules=general_rules,
        uncategorized_category_id=uncategorized_category.id,
    )


def _snapshot_with_keyword_added(
    snapshot: _CategorySnapshot, category_id: int, keyword: str
) -> _CategorySnapshot:
    new_map = {cid: list(kws) for cid, kws in snapshot.keywords_by_category_id.items()}
    existing = new_map.setdefault(category_id, [])
    if keyword not in existing:
        existing.append(keyword)
    return _CategorySnapshot(categories=snapshot.categories, keywords_by_category_id=new_map)


def _snapshot_with_keyword_removed(
    snapshot: _CategorySnapshot, category_id: int, keyword: str
) -> _CategorySnapshot:
    new_map = {cid: list(kws) for cid, kws in snapshot.keywords_by_category_id.items()}
    existing = new_map.get(category_id, [])
    new_map[category_id] = [kw for kw in existing if kw != keyword]
    return _CategorySnapshot(categories=snapshot.categories, keywords_by_category_id=new_map)


@dataclass(frozen=True, slots=True)
class CategoryMove:
    """A single transaction's current -> hypothetical-new category move.

    ``new_source`` is whatever the hypothetical categorizer actually
    decided (keyword/transfer/default) — not assumed to be "keyword" —
    so e.g. removing the keyword that was matching a row can correctly
    fall it back to category_source='default' (Uncategorized) rather
    than mislabeling it 'keyword'.
    """

    transaction: Transaction
    new_category_id: int | None
    new_source: str


def preview_add_keyword(
    db: Session, *, category_id: int, keyword: str
) -> list[CategoryMove]:
    """Candidate transactions that would change category if `keyword`
    were added to `category_id`, under full categorizer precedence.

    Only non-manual transactions are candidates (manual rows are
    sticky and never considered). A transaction only appears in the
    result if the hypothetical categorizer's verdict differs from its
    *current* category_id — i.e. the new keyword actually wins against
    whatever else would otherwise match it.
    """
    keyword_upper = keyword.upper().strip()
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_with_keyword_added(snapshot, category_id, keyword_upper)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_source != "manual")
            .where(Transaction.normalized_description.like(f"%{keyword_upper}%"))
        )
        .scalars()
        .all()
    )

    moves: list[CategoryMove] = []
    for txn in candidates:
        result = hypothetical.categorize(txn.normalized_description)
        if result.category_id != txn.category_id:
            moves.append(
                CategoryMove(
                    transaction=txn, new_category_id=result.category_id, new_source=result.source
                )
            )
    return moves


def preview_remove_keyword(
    db: Session, *, category_id: int, keyword: str
) -> list[CategoryMove]:
    """Candidate transactions currently matched BY this exact keyword
    (i.e. the keyword is a substring of their normalized_description
    and they're in the owning category) that would land elsewhere if
    the keyword were removed. Manual rows are never candidates."""
    keyword_upper = keyword.upper().strip()
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_with_keyword_removed(snapshot, category_id, keyword_upper)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_source != "manual")
            .where(Transaction.normalized_description.like(f"%{keyword_upper}%"))
        )
        .scalars()
        .all()
    )

    moves: list[CategoryMove] = []
    for txn in candidates:
        result = hypothetical.categorize(txn.normalized_description)
        if result.category_id != txn.category_id:
            moves.append(
                CategoryMove(
                    transaction=txn, new_category_id=result.category_id, new_source=result.source
                )
            )
    return moves


def apply_moves(db: Session, moves: list[CategoryMove]) -> int:
    """Apply a list of CategoryMove results, setting category_id and
    category_source to whatever the hypothetical categorizer decided
    for each row. Returns the number of rows updated. Does not commit."""
    count = 0
    for move in moves:
        move.transaction.category_id = move.new_category_id
        move.transaction.category_source = move.new_source
        count += 1
    return count
