from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.parsers.amex import AmexParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("amex_happy.csv"))
    result = AmexParser.parse(text, "amex_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3


def test_amount_sign_is_inverted_positive_charge_becomes_negative() -> None:
    text = read_text(fixture_path("amex_happy.csv"))
    result = AmexParser.parse(text, "amex_happy.csv")

    first = result.transactions[0]
    assert first.txn_date == date(2026, 11, 12)
    assert first.amount == Decimal("-5.00")  # positive charge -> negative (money out)


def test_account_hint_strips_leading_minus() -> None:
    text = read_text(fixture_path("amex_happy.csv"))
    result = AmexParser.parse(text, "amex_happy.csv")

    assert result.transactions[0].account_hint == "21003"
    assert result.transactions[2].account_hint == "21029"


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("amex_malformed.csv"))
    result = AmexParser.parse(text, "amex_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
    assert result.failures[0].line_number == 3


def test_normalized_description_collapses_whitespace_and_uppercases() -> None:
    text = read_text(fixture_path("amex_happy.csv"))
    result = AmexParser.parse(text, "amex_happy.csv")

    first = result.transactions[0]
    assert first.description == "OBSIDIAN            OAKVILLE"
    assert first.normalized_description == "OBSIDIAN OAKVILLE"
