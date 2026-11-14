from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.parsers.capital_one import CapitalOneParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("capital_one_happy.csv"))
    result = CapitalOneParser.parse(text, "capital_one_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3
    assert result.institution_code == "capital_one"


def test_debit_is_negative_credit_is_positive() -> None:
    text = read_text(fixture_path("capital_one_happy.csv"))
    result = CapitalOneParser.parse(text, "capital_one_happy.csv")

    credit_row = result.transactions[0]  # Credit=14.32
    assert credit_row.amount == Decimal("14.32")

    debit_row = result.transactions[2]  # Debit=70.00
    assert debit_row.amount == Decimal("-70.00")


def test_bank_category_is_preserved() -> None:
    text = read_text(fixture_path("capital_one_happy.csv"))
    result = CapitalOneParser.parse(text, "capital_one_happy.csv")

    assert result.transactions[0].bank_category == "Merchandise"


def test_account_hint_is_card_no() -> None:
    text = read_text(fixture_path("capital_one_happy.csv"))
    result = CapitalOneParser.parse(text, "capital_one_happy.csv")

    assert result.transactions[0].account_hint == "9261"
    assert result.transactions[1].account_hint == "0889"


def test_dates_parsed_from_yyyy_mm_dd() -> None:
    text = read_text(fixture_path("capital_one_happy.csv"))
    result = CapitalOneParser.parse(text, "capital_one_happy.csv")

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 6)
    assert first.posted_date == date(2026, 11, 9)


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("capital_one_malformed.csv"))
    result = CapitalOneParser.parse(text, "capital_one_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
    assert result.failures[0].line_number == 3
