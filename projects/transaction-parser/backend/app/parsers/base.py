"""Base parser machinery shared by every bank-specific parser.

Parsers are pure: they take raw CSV text + a filename and return a
``ParseResult``. They never import SQLAlchemy or touch the database.
Per-row failures are isolated so one malformed row never aborts the
whole file.
"""
from __future__ import annotations

import csv
import io
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from app.domain import ParsedTransaction, ParseResult, RowFailure

_WHITESPACE_RE = re.compile(r"\s+")
_MONEY_STRIP_RE = re.compile(r"[,\s]")


def parse_money(raw: str) -> Decimal:
    """Parse a bank-formatted money string into an unsigned-aware Decimal.

    Handles: ``$12.34``, ``1,234.56``, leading/trailing minus, and the
    sign-before-dollar-sign form used by Citi (``-$ 345.33`` /
    `` -$ 1,332.10``). The returned Decimal keeps whatever sign was
    present in the input; callers apply the bank's own sign convention
    (debit/credit column, inverted Amex amount, etc.) on top of this.

    Raises ``InvalidOperation`` (via Decimal) or ``ValueError`` if the
    string cannot be interpreted as a number.
    """
    if raw is None:
        raise ValueError("empty money value")

    s = raw.strip()
    if not s:
        raise ValueError("empty money value")

    negative = False

    # Handle a leading or trailing minus sign that may appear before or
    # after the dollar sign, e.g. "-$345.33", "$-345.33", "345.33-".
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    if s.endswith("-"):
        negative = True
        s = s[:-1].strip()

    s = s.replace("$", "").strip()

    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    if s.endswith("-"):
        negative = True
        s = s[:-1].strip()

    # Parentheses as a negative indicator, e.g. "(345.33)".
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    s = _MONEY_STRIP_RE.sub("", s)
    if not s:
        raise ValueError(f"could not parse money value: {raw!r}")

    value = Decimal(s)
    return -value if negative else value


def parse_date(raw: str, fmt: str) -> date:
    """Parse a date string using the given strptime format."""
    s = raw.strip()
    if not s:
        raise ValueError("empty date value")
    return datetime.strptime(s, fmt).date()


def normalize_description(raw: str) -> str:
    """Uppercase, collapse internal whitespace runs, and strip."""
    collapsed = _WHITESPACE_RE.sub(" ", raw.strip())
    return collapsed.upper()


def _reconcile_field_count(raw_fields: list[str], expected: int) -> list[str]:
    """Recover from an extra, unescaped comma inside an otherwise
    unquoted field (seen in real Citi exports, e.g. a thousands
    separator inside `` -$ 1,332.10`` that isn't wrapped in quotes).

    When ``csv.reader`` yields more fields than the header has columns,
    the extra commas are assumed to have split a single value near the
    end of the row (but before the final, reliably-intact trailing
    column). We rejoin the surplus fields back together with a comma
    so the row lines up with the header again. Rows with the expected
    field count, or fewer, pass through unchanged.
    """
    surplus = len(raw_fields) - expected
    if surplus <= 0:
        return raw_fields

    # Merge the surplus fields starting one before the final column,
    # preserving the last column intact (e.g. "MEMBER NAME").
    merge_start = max(expected - 2, 0)
    merge_end = merge_start + surplus + 1
    merged_chunk = ",".join(raw_fields[merge_start:merge_end])
    return raw_fields[:merge_start] + [merged_chunk] + raw_fields[merge_end:]


class BaseParser(ABC):
    """Template-method base class for all bank CSV parsers.

    Subclasses declare ``institution_code``, ``expected_header``, and
    ``account_kind``, and implement ``parse_row``. The base class owns
    the CSV iteration, blank-row skipping, and per-row error isolation.
    """

    institution_code: ClassVar[str]
    expected_header: ClassVar[tuple[str, ...]]
    account_kind: ClassVar[str]

    @classmethod
    def matches_header(cls, header: tuple[str, ...]) -> bool:
        """Exact (order-sensitive) header match."""
        return header == cls.expected_header

    @classmethod
    def parse(cls, text: str, filename: str) -> ParseResult:
        """Parse CSV text into a ParseResult.

        Blank rows (all fields empty/whitespace) are silently skipped.
        Any other row that raises during ``parse_row`` becomes a
        ``RowFailure`` and parsing continues with the next row.
        """
        reader = csv.reader(io.StringIO(text))
        try:
            header_row = next(reader)
        except StopIteration:
            return ParseResult(institution_code=cls.institution_code)

        fieldnames = [h.strip() for h in header_row]
        transactions: list[ParsedTransaction] = []
        failures: list[RowFailure] = []

        line_no = 1  # header is line 1
        for raw_fields in reader:
            line_no += 1

            if not any(field.strip() for field in raw_fields):
                continue  # fully-blank row, skip silently

            raw_line = ",".join(raw_fields)
            try:
                fields = _reconcile_field_count(raw_fields, len(fieldnames))
                row = dict(zip(fieldnames, fields, strict=False))
                txn = cls.parse_row(row, line_no)
                transactions.append(txn)
            except Exception as exc:  # noqa: BLE001 - isolate any row failure
                failures.append(
                    RowFailure(
                        line_number=line_no,
                        raw_line=raw_line,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )

        return ParseResult(
            institution_code=cls.institution_code,
            transactions=transactions,
            failures=failures,
        )

    @classmethod
    @abstractmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction:
        """Parse a single CSV row (as a dict keyed by header) into a
        ``ParsedTransaction``. Raise any exception to isolate the row
        as a failure; the base class catches it."""
        raise NotImplementedError
