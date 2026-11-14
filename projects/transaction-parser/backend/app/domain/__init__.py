"""Pure domain objects for the parsing layer.

These dataclasses carry data between the CSV parsers and the ingest
service. They never touch SQLAlchemy or the database — parsers are pure
functions of (text, filename) -> ParseResult.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ParsedTransaction:
    """A single successfully parsed transaction row.

    Sign convention: negative = money out, positive = money in. This is
    normalized by each parser regardless of the source bank's own
    convention (e.g. Amex's positive-is-charge is inverted on parse).
    """

    txn_date: date
    posted_date: date | None
    description: str
    normalized_description: str
    amount: Decimal
    account_hint: str
    bank_category: str | None
    raw_row: dict[str, str]
    line_number: int


@dataclass(frozen=True, slots=True)
class RowFailure:
    """A single row that failed to parse; parsing continues past it."""

    line_number: int
    raw_line: str
    error_type: str
    error_message: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    """The outcome of parsing one file: successes plus isolated failures."""

    institution_code: str
    transactions: list[ParsedTransaction] = field(default_factory=list)
    failures: list[RowFailure] = field(default_factory=list)
