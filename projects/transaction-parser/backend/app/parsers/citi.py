"""Citi CSV parser.

Format quirks:
- Filename extension is uppercase ``.CSV`` (handled by case-insensitive
  extension validation in registry.py, not here).
- Date format MM/DD/YYYY, no separate posted date.
- Amounts are formatted as ``$ 27.95`` (space after the dollar sign).
- Credits are already negative with the sign *before* the dollar sign,
  e.g. `` -$ 345.33`` or `` -$ 1,332.10``; ``parse_money`` handles this
  form directly, so we take the absolute value and apply our own
  positive-for-money-in convention.
- No account column at all; account hint is the fixed string "citi".
"""
from __future__ import annotations

from app.domain import ParsedTransaction
from app.parsers.base import BaseParser, normalize_description, parse_date, parse_money

_DATE_FMT = "%m/%d/%Y"


class CitiParser(BaseParser):
    institution_code = "citi"
    account_kind = "card"
    expected_header = ("Status", "Date", "Description", "Debit", "Credit", "Member Name")

    @classmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction:
        txn_date = parse_date(row["Date"], _DATE_FMT)
        description = row["Description"].strip()

        debit_raw = row.get("Debit", "").strip()
        credit_raw = row.get("Credit", "").strip()

        if debit_raw:
            amount = -abs(parse_money(debit_raw))
        elif credit_raw:
            amount = abs(parse_money(credit_raw))
        else:
            raise ValueError("row has neither Debit nor Credit value")

        return ParsedTransaction(
            txn_date=txn_date,
            posted_date=None,
            description=description,
            normalized_description=normalize_description(description),
            amount=amount,
            account_hint="citi",
            bank_category=None,
            raw_row=dict(row),
            line_number=line_no,
        )
