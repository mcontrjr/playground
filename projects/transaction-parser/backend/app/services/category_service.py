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

from app.models import Category, CategoryKeyword, ClashDismissal, Transaction
from app.services.categorizer import (
    TRANSFER_CATEGORY_NAME,
    UNCATEGORIZED_CATEGORY_NAME,
    Categorizer,
    CategorizerConfigError,
    ClashReport,
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


def _snapshot_without_category(
    snapshot: _CategorySnapshot, category_id: int
) -> _CategorySnapshot:
    """Drop a category and all of its keywords, as deleting it would."""
    new_map = {
        cid: list(kws)
        for cid, kws in snapshot.keywords_by_category_id.items()
        if cid != category_id
    }
    return _CategorySnapshot(
        categories=[c for c in snapshot.categories if c.id != category_id],
        keywords_by_category_id=new_map,
    )


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
    new_matched_keyword: str | None = None
    """The keyword behind ``new_source``; null when the result was
    'default' (nothing matched). Carried so applying a move keeps
    matched_keyword consistent with the category it writes."""


def preview_add_keyword(
    db: Session, *, category_id: int, keyword: str
) -> list[CategoryMove]:
    """Candidate transactions that would change category if `keyword`
    were added to `category_id`, under full categorizer precedence.

    Only non-sticky transactions are candidates (manual and bulk rows
    are sticky and never considered — both represent a deliberate user
    choice of category, same as a single manual edit). A transaction
    only appears in the result if the hypothetical categorizer's
    verdict differs from its *current* category_id — i.e. the new
    keyword actually wins against whatever else would otherwise match
    it.
    """
    keyword_upper = keyword.upper().strip()
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_with_keyword_added(snapshot, category_id, keyword_upper)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_source.not_in(["manual", "bulk"]))
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
                    transaction=txn,
                    new_category_id=result.category_id,
                    new_source=result.source,
                    new_matched_keyword=result.matched_keyword,
                )
            )
    return moves


def preview_remove_keyword(
    db: Session, *, category_id: int, keyword: str
) -> list[CategoryMove]:
    """Candidate transactions currently matched BY this exact keyword
    (i.e. the keyword is a substring of their normalized_description
    and they're in the owning category) that would land elsewhere if
    the keyword were removed. Manual and bulk rows are never
    candidates."""
    keyword_upper = keyword.upper().strip()
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_with_keyword_removed(snapshot, category_id, keyword_upper)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_source.not_in(["manual", "bulk"]))
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
                    transaction=txn,
                    new_category_id=result.category_id,
                    new_source=result.source,
                    new_matched_keyword=result.matched_keyword,
                )
            )
    return moves


@dataclass(frozen=True, slots=True)
class TransactionClash:
    """One transaction whose description is claimed by more than one
    category, together with the claims and how it currently sits.

    ``is_settled`` means the user already had the final say on this row
    (manual or bulk): the clash still *exists* as a rule ambiguity, but
    there is nothing to ask — their choice stands, permanently.
    """

    transaction: Transaction
    report: ClashReport
    is_settled: bool

    @property
    def competing_category_ids(self) -> list[int]:
        return list(dict.fromkeys(c.category_id for c in self.report.claims))


def _load_dismissals(db: Session) -> tuple[set[tuple[int, int]], set[tuple[int, int, int]]]:
    """Dismissed pairings, as (rule_level, row_level) lookup sets.

    Rule-level keys are ``(winner_id, loser_id)``; row-level keys add the
    transaction id. Loaded once per clash scan so the filter below is a
    set membership test rather than a query per row.
    """
    rules: set[tuple[int, int]] = set()
    rows: set[tuple[int, int, int]] = set()
    for d in db.execute(select(ClashDismissal)).scalars().all():
        if d.transaction_id is None:
            rules.add((d.winner_category_id, d.loser_category_id))
        else:
            rows.add((d.winner_category_id, d.loser_category_id, d.transaction_id))
    return rules, rows


def _is_dismissed(
    clash: TransactionClash,
    rules: set[tuple[int, int]],
    rows: set[tuple[int, int, int]],
) -> bool:
    """True when the user already judged this conflict fine.

    A dismissal covers one winner-vs-loser pairing. A row claimed by
    three categories is only hidden once *every* losing claim has been
    dismissed against the current winner — otherwise a still-unreviewed
    competitor would be silently suppressed along with the reviewed one.
    """
    winner = clash.report.winner
    if winner is None:
        return False

    losers = [c.category_id for c in clash.report.claims if c.category_id != winner.category_id]
    if not losers:
        return False

    txn_id = clash.transaction.id
    return all(
        (winner.category_id, loser) in rules
        or (winner.category_id, loser, txn_id) in rows
        for loser in losers
    )


def find_clashes(
    db: Session, *, include_settled: bool = False, include_dismissed: bool = False
) -> list[TransactionClash]:
    """Every transaction whose description is claimed by two or more
    categories, i.e. where the categorizer silently picked a winner.

    By default only unsettled, non-dismissed rows are returned — the ones
    still needing a decision. ``include_settled`` also returns manual/bulk
    rows (never actionable); ``include_dismissed`` also returns pairings
    the user already judged correct.
    """
    categorizer = Categorizer.load(db)
    rules, rows = _load_dismissals(db)

    clashes: list[TransactionClash] = []
    for txn in db.execute(select(Transaction)).scalars().all():
        report = categorizer.explain(txn.normalized_description)
        if not report.is_clash:
            continue
        settled = txn.category_source in ("manual", "bulk")
        if settled and not include_settled:
            continue
        clash = TransactionClash(transaction=txn, report=report, is_settled=settled)
        if not include_dismissed and _is_dismissed(clash, rules, rows):
            continue
        clashes.append(clash)
    return clashes


def count_dismissed_clashes(db: Session) -> int:
    """How many live clashing rows are currently hidden by a dismissal.

    Counted against real transactions rather than dismissal rows, so one
    rule-level dismissal covering nine Uber rows reports nine — which is
    what "N dismissed" in the UI should mean.
    """
    categorizer = Categorizer.load(db)
    rules, rows = _load_dismissals(db)

    hidden = 0
    for txn in db.execute(select(Transaction)).scalars().all():
        report = categorizer.explain(txn.normalized_description)
        if not report.is_clash:
            continue
        clash = TransactionClash(
            transaction=txn,
            report=report,
            is_settled=txn.category_source in ("manual", "bulk"),
        )
        if _is_dismissed(clash, rules, rows):
            hidden += 1
    return hidden


def clashes_for_keyword(db: Session, *, category_id: int, keyword: str) -> list[TransactionClash]:
    """Rows that would be claimed by BOTH ``category_id`` (via the
    hypothetical new ``keyword``) and some other category.

    Used to warn at the moment a keyword is added: these are the rows
    where adding it creates an ambiguity that priority — not the user —
    would silently resolve. Settled rows are excluded, since the user's
    choice already governs them.
    """
    keyword_upper = keyword.upper().strip()
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_with_keyword_added(snapshot, category_id, keyword_upper)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_source.not_in(["manual", "bulk"]))
            .where(Transaction.normalized_description.like(f"%{keyword_upper}%"))
        )
        .scalars()
        .all()
    )

    clashes: list[TransactionClash] = []
    for txn in candidates:
        report = hypothetical.explain(txn.normalized_description)
        if report.is_clash:
            clashes.append(
                TransactionClash(transaction=txn, report=report, is_settled=False)
            )
    return clashes


def dismiss_clash(
    db: Session,
    *,
    winner_category_id: int,
    loser_category_id: int,
    transaction_id: int | None = None,
    note: str | None = None,
) -> ClashDismissal:
    """Record that a conflict is correct as-is, so it stops being listed.

    Leaves the transaction's categorization completely untouched — this
    is a judgment about the rules, not about the row. That's the whole
    difference from ``resolve_clash``, which pins the row as 'manual'
    and thereby opts it out of every future rule change.

    Idempotent: re-dismissing the same scope returns the existing row
    rather than violating the partial unique index.
    """
    existing = db.execute(
        select(ClashDismissal)
        .where(ClashDismissal.winner_category_id == winner_category_id)
        .where(ClashDismissal.loser_category_id == loser_category_id)
        .where(ClashDismissal.transaction_id == transaction_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    dismissal = ClashDismissal(
        winner_category_id=winner_category_id,
        loser_category_id=loser_category_id,
        transaction_id=transaction_id,
        note=note,
    )
    db.add(dismissal)
    db.flush()
    return dismissal


def undismiss_clash(db: Session, *, dismissal_id: int) -> bool:
    """Drop a dismissal so its conflicts return to the queue."""
    dismissal = db.get(ClashDismissal, dismissal_id)
    if dismissal is None:
        return False
    db.delete(dismissal)
    db.flush()
    return True


def resolve_clash(
    db: Session,
    *,
    transaction_ids: list[int],
    category_id: int,
) -> int:
    """Settle a clash by the user's explicit choice: pin the given rows
    to ``category_id`` with ``category_source='manual'``.

    'manual' is deliberate — it makes the decision permanently sticky,
    so neither a future keyword add, a priority reorder, nor a
    recategorize-all pass can silently undo what the user chose here.
    Does not commit.
    """
    rows = (
        db.execute(select(Transaction).where(Transaction.id.in_(transaction_ids)))
        .scalars()
        .all()
    )
    for txn in rows:
        txn.category_id = category_id
        txn.category_source = "manual"
        # A person chose this; no keyword decided it.
        txn.matched_keyword = None
    return len(rows)


def preview_delete_category(db: Session, *, category_id: int) -> list[CategoryMove]:
    """Where this category's transactions would land if it were deleted
    and the remaining rules were re-run.

    Deleting a category removes its keywords too, so its rows have to go
    somewhere: this reports where each one would actually match — which
    is often a real category (FOOD, STREAMING) rather than Uncategorized.
    Rows nothing claims come back as 'default' (Uncategorized), which is
    the honest answer for them specifically rather than for all of them.

    Manual and bulk rows are excluded: their category was chosen by a
    person. They still get reassigned off the deleted category by the
    delete itself (the FK would dangle otherwise), but they are not the
    rules' business to re-match.
    """
    snapshot = _load_snapshot(db)
    hypothetical = _build_categorizer_from_snapshot(
        _snapshot_without_category(snapshot, category_id)
    )

    candidates = (
        db.execute(
            select(Transaction)
            .where(Transaction.category_id == category_id)
            .where(Transaction.category_source.not_in(["manual", "bulk"]))
        )
        .scalars()
        .all()
    )

    moves: list[CategoryMove] = []
    for txn in candidates:
        result = hypothetical.categorize(txn.normalized_description)
        moves.append(
            CategoryMove(
                transaction=txn,
                new_category_id=result.category_id,
                new_source=result.source,
                new_matched_keyword=result.matched_keyword,
            )
        )
    return moves


def preview_recategorize_all(db: Session) -> list[CategoryMove]:
    """Every non-sticky transaction whose category would change if the
    *current* rules were re-run over it.

    Categorization normally happens only once, at ingest time, so a row
    keeps whatever category it got when it was first inserted. Keywords
    added or re-prioritized afterwards therefore never reach rows that
    predate the change — `apply_to_existing` covers that for a single
    keyword add/remove, but nothing covers a priority edit, a seed
    change, or an accumulated backlog. This is the catch-up pass: it
    diffs the live rules against every existing row.

    Unlike the keyword previews, there's no hypothetical mutation and no
    description filter — the comparison is the real categorizer against
    all candidate rows, so a move here means "this row's stored
    category disagrees with what the rules say today".

    Manual and bulk rows are excluded, same as every other apply path:
    a deliberate user choice outranks the rules.
    """
    categorizer = Categorizer.load(db)

    candidates = (
        db.execute(
            select(Transaction).where(Transaction.category_source.not_in(["manual", "bulk"]))
        )
        .scalars()
        .all()
    )

    moves: list[CategoryMove] = []
    for txn in candidates:
        result = categorizer.categorize(txn.normalized_description)
        if result.category_id != txn.category_id:
            moves.append(
                CategoryMove(
                    transaction=txn,
                    new_category_id=result.category_id,
                    new_source=result.source,
                    new_matched_keyword=result.matched_keyword,
                )
            )
    return moves


def preview_reprioritize(
    db: Session, *, priorities: dict[int, int]
) -> list[CategoryMove]:
    """Rows that would change category if categories were re-prioritized
    to ``priorities`` (category_id -> new priority).

    Priority is global, so a reorder intended to fix one merchant can
    move unrelated rows that happen to share a keyword — this is what
    makes that blast radius visible before anything is written. Mirrors
    the keyword previews: a hypothetical snapshot, the real categorizer,
    and sticky rows excluded.
    """
    snapshot = _load_snapshot(db)

    # Re-prioritize on detached copies so the caller's session is never
    # left holding speculative priority values it might flush.
    originals = {c.id: c.priority for c in snapshot.categories}
    try:
        for category in snapshot.categories:
            if category.id in priorities:
                category.priority = priorities[category.id]
        hypothetical = _build_categorizer_from_snapshot(snapshot)

        candidates = (
            db.execute(
                select(Transaction).where(
                    Transaction.category_source.not_in(["manual", "bulk"])
                )
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
                        transaction=txn,
                        new_category_id=result.category_id,
                        new_source=result.source,
                        new_matched_keyword=result.matched_keyword,
                    )
                )
        return moves
    finally:
        for category in snapshot.categories:
            category.priority = originals[category.id]
        db.expire_all()


def apply_moves(db: Session, moves: list[CategoryMove]) -> int:
    """Apply a list of CategoryMove results, setting category_id and
    category_source to whatever the hypothetical categorizer decided
    for each row. Returns the number of rows updated. Does not commit."""
    count = 0
    for move in moves:
        move.transaction.category_id = move.new_category_id
        move.transaction.category_source = move.new_source
        move.transaction.matched_keyword = move.new_matched_keyword
        count += 1
    return count
