from __future__ import annotations

from decimal import Decimal

from app.parsers.citi import CitiParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("citi_happy.csv"))
    result = CitiParser.parse(text, "citi_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3
    assert result.institution_code == "citi"


def test_debit_dollar_space_amount_is_negative() -> None:
    text = read_text(fixture_path("citi_happy.csv"))
    result = CitiParser.parse(text, "citi_happy.csv")

    assert result.transactions[0].amount == Decimal("-27.95")


def test_credit_sign_before_dollar_sign_case() -> None:
    """The ' -$ 345.33' form: sign precedes the dollar sign."""
    text = read_text(fixture_path("citi_happy.csv"))
    result = CitiParser.parse(text, "citi_happy.csv")

    assert result.transactions[1].amount == Decimal("345.33")


def test_credit_thousands_comma_with_unescaped_split() -> None:
    """' -$ 1,332.10' — the thousands comma is unquoted in the real
    export and splits the row into an extra CSV field; the parser must
    reconcile the field count and still parse correctly."""
    text = read_text(fixture_path("citi_happy.csv"))
    result = CitiParser.parse(text, "citi_happy.csv")

    assert result.transactions[2].amount == Decimal("1332.10")


def test_account_hint_is_fixed_citi_string() -> None:
    text = read_text(fixture_path("citi_happy.csv"))
    result = CitiParser.parse(text, "citi_happy.csv")

    assert all(t.account_hint == "citi" for t in result.transactions)


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("citi_malformed.csv"))
    result = CitiParser.parse(text, "citi_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
