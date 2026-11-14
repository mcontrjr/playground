"""Schwab checking CSV parser.

Format quirks:
- All fields are quoted.
- Date format MM/DD/YYYY, no separate posted date.
- Amounts may use thousands-separator commas, e.g. ``$4,130.32``.
- ``Withdrawal`` -> money out (negative), ``Deposit`` -> money in
  (positive). Extra ``Type``/``CheckNumber``/``RunningBalance`` columns
  are ignored (preserved only in raw_row).
- Account hint is the fixed string "checking". This file includes the
  payment-side of card statements (e.g. "CITI CARD ONLINE PAYMENT").
"""
from __future__ import annotations

from app.domain import ParsedTransaction
from app.parsers.base import BaseParser, normalize_description, parse_date, parse_money

_DATE_FMT = "%m/%d/%Y"


class SchwabParser(BaseParser):
    institution_code = "schwab"
    account_kind = "checking"
    expected_header = (
        "Date",
        "Status",
        "Type",
        "CheckNumber",
        "Description",
        "Withdrawal",
        "Deposit",
        "RunningBalance",
    )

    @classmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction:
        txn_date = parse_date(row["Date"], _DATE_FMT)
        description = row["Description"].strip()

        withdrawal_raw = row.get("Withdrawal", "").strip()
        deposit_raw = row.get("Deposit", "").strip()

        if withdrawal_raw:
            amount = -parse_money(withdrawal_raw)
        elif deposit_raw:
            amount = parse_money(deposit_raw)
        else:
            raise ValueError("row has neither Withdrawal nor Deposit value")

        return ParsedTransaction(
            txn_date=txn_date,
            posted_date=None,
            description=description,
            normalized_description=normalize_description(description),
            amount=amount,
            account_hint="checking",
            bank_category=None,
            raw_row=dict(row),
            line_number=line_no,
        )
