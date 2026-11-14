"""Integration-style tests against the 5 real ground-truth sample CSVs
in `transactions/`. Each file must parse with zero failures, and the
transaction count must equal the number of non-blank data rows.
"""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.parsers.amex import AmexParser
from app.parsers.capital_one import CapitalOneParser
from app.parsers.citi import CitiParser
from app.parsers.discover import DiscoverParser
from app.parsers.schwab import SchwabParser
from tests.conftest import read_text, real_file_path


def _count_data_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    data = [row for row in rows[1:] if any(cell.strip() for cell in row)]
    return len(data)


def test_amex_real_file_zero_failures_and_row_count() -> None:
    path = real_file_path("amex_90_day.csv")
    text = read_text(path)
    result = AmexParser.parse(text, path.name)

    assert result.failures == []
    assert len(result.transactions) == _count_data_rows(path)
    assert len(result.transactions) == 105

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 12)
    assert first.description == "OBSIDIAN            OAKVILLE"
    assert first.amount == Decimal("-5.00")
    assert first.account_hint == "21003"


def test_capital_one_real_file_zero_failures_and_row_count() -> None:
    path = real_file_path("capital_one_since_sept.csv")
    text = read_text(path)
    result = CapitalOneParser.parse(text, path.name)

    assert result.failures == []
    assert len(result.transactions) == _count_data_rows(path)
    assert len(result.transactions) == 122

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 6)
    assert first.posted_date == date(2026, 11, 9)
    assert first.description == "HOMEGOODS 0845"
    assert first.amount == Decimal("14.32")
    assert first.account_hint == "9261"
    assert first.bank_category == "Merchandise"


def test_discover_real_file_zero_failures_and_row_count() -> None:
    path = real_file_path("discover_since_sept.csv")
    text = read_text(path)
    result = DiscoverParser.parse(text, path.name)

    assert result.failures == []
    assert len(result.transactions) == _count_data_rows(path)
    assert len(result.transactions) == 61

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 12)
    assert first.description == "CHIPOTLE 1521"
    assert first.amount == Decimal("-17.21")
    assert first.account_hint == "6569"
    assert first.bank_category == "Dining"


def test_citi_real_file_zero_failures_and_row_count() -> None:
    path = real_file_path("citi_since_sept.CSV")
    text = read_text(path)
    result = CitiParser.parse(text, path.name)

    assert result.failures == []
    assert len(result.transactions) == _count_data_rows(path)
    assert len(result.transactions) == 93

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 8)
    assert first.description == "DD *DOORDASH UNDERGRIN DOORDASH.COM CA"
    assert first.amount == Decimal("-27.95")
    assert first.account_hint == "citi"

    # The known thousands-comma-credit row (unescaped comma in the real
    # export) must still parse correctly.
    thousands_row = next(
        t for t in result.transactions if t.txn_date == date(2026, 9, 27)
    )
    assert thousands_row.amount == Decimal("1332.10")


def test_schwab_real_file_zero_failures_and_row_count() -> None:
    path = real_file_path("schwab_since_sept.csv")
    text = read_text(path)
    result = SchwabParser.parse(text, path.name)

    assert result.failures == []
    assert len(result.transactions) == _count_data_rows(path)
    assert len(result.transactions) == 67

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 13)
    assert first.description == "SERVE OPERATING PAYROLL"
    assert first.amount == Decimal("4130.32")
    assert first.account_hint == "checking"
