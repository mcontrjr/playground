"""American Express CSV parser.

Format quirks:
- Date format MM/DD/YYYY, no separate posted date.
- Single signed ``Amount`` column where positive means a charge (money
  out) — inverted relative to our internal convention, so we negate it.
- ``Account #`` is a literal-minus-prefixed last-5, e.g. ``-21003``; the
  account hint strips the leading ``-`` to ``21003``.
- Descriptions may be fixed-width padded with internal runs of spaces,
  which ``normalize_description`` collapses.
"""
from __future__ import annotations

from app.domain import ParsedTransaction
from app.parsers.base import BaseParser, normalize_description, parse_date, parse_money

_DATE_FMT = "%m/%d/%Y"


class AmexParser(BaseParser):
    institution_code = "amex"
    account_kind = "card"
    expected_header = ("Date", "Description", "Card Member", "Account #", "Amount")

    @classmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction:
        txn_date = parse_date(row["Date"], _DATE_FMT)
        description = row["Description"].strip()
        amount = -parse_money(row["Amount"])  # positive=charge -> negate
        account_hint = row["Account #"].strip().lstrip("-")

        return ParsedTransaction(
            txn_date=txn_date,
            posted_date=None,
            description=description,
            normalized_description=normalize_description(description),
            amount=amount,
            account_hint=account_hint,
            bank_category=None,
            raw_row=dict(row),
            line_number=line_no,
        )
