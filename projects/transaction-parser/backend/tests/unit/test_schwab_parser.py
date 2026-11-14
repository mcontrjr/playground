from __future__ import annotations

from decimal import Decimal

from app.parsers.schwab import SchwabParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("schwab_happy.csv"))
    result = SchwabParser.parse(text, "schwab_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3
    assert result.institution_code == "schwab"


def test_deposit_with_thousands_comma_is_positive() -> None:
    text = read_text(fixture_path("schwab_happy.csv"))
    result = SchwabParser.parse(text, "schwab_happy.csv")

    first = result.transactions[0]
    assert first.amount == Decimal("4130.32")


def test_withdrawal_is_negative() -> None:
    text = read_text(fixture_path("schwab_happy.csv"))
    result = SchwabParser.parse(text, "schwab_happy.csv")

    assert result.transactions[1].amount == Decimal("-345.33")
    assert result.transactions[2].amount == Decimal("-200.00")


def test_account_hint_is_fixed_checking_string() -> None:
    text = read_text(fixture_path("schwab_happy.csv"))
    result = SchwabParser.parse(text, "schwab_happy.csv")

    assert all(t.account_hint == "checking" for t in result.transactions)


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("schwab_malformed.csv"))
    result = SchwabParser.parse(text, "schwab_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
