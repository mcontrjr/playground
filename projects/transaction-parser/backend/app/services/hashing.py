"""Pure idempotency hashing logic, shared by the ingest service.

``content_hash`` excludes posted_date and filename so overlapping
re-exports from the same bank dedupe correctly. Within a single file,
rows that hash identically are assigned increasing ``occurrence_index``
values in file order, so legitimate duplicate purchases (e.g. two
identical $5 coffees on the same day) both survive, while re-uploading
the same file reproduces the same indices and therefore dedupes
against whatever was already inserted.
"""
from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

from app.domain import ParsedTransaction


def content_hash(
    institution_code: str,
    account_hint: str,
    txn_date: date,
    amount: Decimal,
    normalized_description: str,
) -> str:
    """Compute the sha256 content hash for a transaction.

    The canonical string is ``institution|account_hint|date_iso|amount|
    normalized_description``, joined with ``|``. ``amount`` is rendered
    via ``str(Decimal)`` quantized to 2 decimal places so formatting is
    stable regardless of how the Decimal was constructed.
    """
    amount_str = str(Decimal(amount).quantize(Decimal("0.01")))
    canonical = "|".join(
        (
            institution_code,
            account_hint,
            txn_date.isoformat(),
            amount_str,
            normalized_description,
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assign_occurrence_indices(
    txns: list[ParsedTransaction],
    institution_code: str,
) -> list[tuple[ParsedTransaction, int]]:
    """Group transactions by their content hash in file order, and
    assign each an occurrence_index 0..n-1 within its hash group.

    ``institution_code`` is required because ``ParsedTransaction``
    itself doesn't carry it (it lives on the enclosing ``ParseResult``)
    but is part of the hash. Pass ``result.institution_code`` when
    calling this against a freshly parsed file.
    """
    seen_counts: dict[str, int] = {}
    result: list[tuple[ParsedTransaction, int]] = []

    for txn in txns:
        h = content_hash(
            institution_code=institution_code,
            account_hint=txn.account_hint,
            txn_date=txn.txn_date,
            amount=txn.amount,
            normalized_description=txn.normalized_description,
        )
        index = seen_counts.get(h, 0)
        seen_counts[h] = index + 1
        result.append((txn, index))

    return result
