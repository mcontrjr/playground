from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.parsers.wells_fargo import WellsFargoParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3
    assert result.institution_code == "wells_fargo"


def test_negative_amount_is_money_out() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert result.transactions[0].amount == Decimal("-9.99")


def test_positive_amount_is_money_in() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert result.transactions[1].amount == Decimal("245.43")
    assert result.transactions[2].amount == Decimal("4400.00")


def test_dates_parse_as_month_day_year() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert result.transactions[0].txn_date == date(2026, 11, 18)
    assert all(t.posted_date is None for t in result.transactions)


def test_account_hint_is_fixed_wells_fargo_string() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert all(t.account_hint == "wells_fargo" for t in result.transactions)


def test_padded_description_kept_raw_and_normalized_collapsed() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    first = result.transactions[0]
    # The source statement pads descriptions with long whitespace runs;
    # the raw form is preserved, the normalized form collapses them.
    assert "    " in first.description
    assert "  " not in first.normalized_description
    assert first.normalized_description.startswith("RECURRING PAYMENT AUTHORIZED ON")


def test_check_number_column_is_preserved_in_raw_row() -> None:
    text = read_text(fixture_path("wells_fargo_happy.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_happy.csv")

    assert result.transactions[0].raw_row["CHECK #"] == ""


def test_pending_rows_are_skipped_without_becoming_failures() -> None:
    text = read_text(fixture_path("wells_fargo_pending.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_pending.csv")

    assert result.failures == []
    assert len(result.transactions) == 2
    assert all(t.raw_row["STATUS"] == "Posted" for t in result.transactions)
    assert all(t.txn_date != date(2026, 11, 20) for t in result.transactions)


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("wells_fargo_malformed.csv"))
    result = WellsFargoParser.parse(text, "wells_fargo_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
    assert result.failures[0].line_number == 3
