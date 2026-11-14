"""Shared base for Capital One and Discover, which share an identical
CSV header and column layout and differ only in institution_code (and
are disambiguated at detection time by filename, see registry.py).

Format quirks (shared):
- Date format YYYY-MM-DD for both Transaction Date and Posted Date.
- Unsigned ``Debit``/``Credit`` columns: a value in Debit is money out
  (negative), a value in Credit is money in (positive). Exactly one of
  the two is populated per row.
- ``Category`` column is the bank's own categorization; preserved as
  ``bank_category``.
- ``Card No.`` is the account hint.
"""
from __future__ import annotations

from app.domain import ParsedTransaction
from app.parsers.base import BaseParser, normalize_description, parse_date, parse_money

_DATE_FMT = "%Y-%m-%d"

_SHARED_HEADER = (
    "Transaction Date",
    "Posted Date",
    "Card No.",
    "Description",
    "Category",
    "Debit",
    "Credit",
)


class CapOneDiscoverBaseParser(BaseParser):
    """Not registered directly — subclasses set institution_code."""

    account_kind = "card"
    expected_header = _SHARED_HEADER

    @classmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction:
        txn_date = parse_date(row["Transaction Date"], _DATE_FMT)
        posted_raw = row.get("Posted Date", "").strip()
        posted_date = parse_date(posted_raw, _DATE_FMT) if posted_raw else None

        description = row["Description"].strip()
        debit_raw = row.get("Debit", "").strip()
        credit_raw = row.get("Credit", "").strip()

        if debit_raw:
            amount = -parse_money(debit_raw)
        elif credit_raw:
            amount = parse_money(credit_raw)
        else:
            raise ValueError("row has neither Debit nor Credit value")

        bank_category = row.get("Category", "").strip() or None

        return ParsedTransaction(
            txn_date=txn_date,
            posted_date=posted_date,
            description=description,
            normalized_description=normalize_description(description),
            amount=amount,
            account_hint=row["Card No."].strip(),
            bank_category=bank_category,
            raw_row=dict(row),
            line_number=line_no,
        )
