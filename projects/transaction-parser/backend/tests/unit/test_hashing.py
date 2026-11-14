from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.domain import ParsedTransaction
from app.services.hashing import assign_occurrence_indices, content_hash


def _txn(
    *,
    amount: str = "-5.00",
    description: str = "COFFEE SHOP",
    txn_date: date = date(2026, 11, 12),
    account_hint: str = "21003",
    line_number: int = 2,
) -> ParsedTransaction:
    return ParsedTransaction(
        txn_date=txn_date,
        posted_date=None,
        description=description,
        normalized_description=description,
        amount=Decimal(amount),
        account_hint=account_hint,
        bank_category=None,
        raw_row={},
        line_number=line_number,
    )


def test_identical_rows_get_indices_0_and_1() -> None:
    txns = [_txn(line_number=2), _txn(line_number=3)]
    result = assign_occurrence_indices(txns, institution_code="amex")

    assert [idx for _, idx in result] == [0, 1]


def test_distinct_rows_each_get_index_0() -> None:
    txns = [_txn(line_number=2), _txn(line_number=3, description="DIFFERENT MERCHANT")]
    result = assign_occurrence_indices(txns, institution_code="amex")

    assert [idx for _, idx in result] == [0, 0]


def test_reparse_yields_identical_hash_and_index_pairs() -> None:
    txns = [_txn(line_number=2), _txn(line_number=3)]

    first_pass = [
        (content_hash("amex", t.account_hint, t.txn_date, t.amount, t.normalized_description), idx)
        for t, idx in assign_occurrence_indices(txns, institution_code="amex")
    ]
    second_pass = [
        (content_hash("amex", t.account_hint, t.txn_date, t.amount, t.normalized_description), idx)
        for t, idx in assign_occurrence_indices(txns, institution_code="amex")
    ]

    assert first_pass == second_pass


def test_differing_amounts_produce_different_hashes() -> None:
    txn_a = _txn(amount="-5.00")
    txn_b = _txn(amount="-6.00")

    hash_a = content_hash(
        "amex", txn_a.account_hint, txn_a.txn_date, txn_a.amount, txn_a.normalized_description
    )
    hash_b = content_hash(
        "amex", txn_b.account_hint, txn_b.txn_date, txn_b.amount, txn_b.normalized_description
    )

    assert hash_a != hash_b


def test_differing_institution_produces_different_hash() -> None:
    txn = _txn()
    hash_amex = content_hash(
        "amex", txn.account_hint, txn.txn_date, txn.amount, txn.normalized_description
    )
    hash_citi = content_hash(
        "citi", txn.account_hint, txn.txn_date, txn.amount, txn.normalized_description
    )
    assert hash_amex != hash_citi
