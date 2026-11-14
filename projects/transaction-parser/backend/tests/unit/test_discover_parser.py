from __future__ import annotations

from decimal import Decimal

from app.parsers.discover import DiscoverParser
from tests.conftest import fixture_path, read_text


def test_happy_path_parses_all_rows() -> None:
    text = read_text(fixture_path("discover_happy.csv"))
    result = DiscoverParser.parse(text, "discover_happy.csv")

    assert result.failures == []
    assert len(result.transactions) == 3
    assert result.institution_code == "discover"


def test_debit_is_negative() -> None:
    text = read_text(fixture_path("discover_happy.csv"))
    result = DiscoverParser.parse(text, "discover_happy.csv")

    assert result.transactions[0].amount == Decimal("-17.21")


def test_quoted_comma_in_description_is_preserved() -> None:
    text = read_text(fixture_path("discover_happy.csv"))
    result = DiscoverParser.parse(text, "discover_happy.csv")

    assert result.transactions[1].description == "DD *DOORDASH, JERSEYMIK"


def test_malformed_row_is_isolated_and_parsing_continues() -> None:
    text = read_text(fixture_path("discover_malformed.csv"))
    result = DiscoverParser.parse(text, "discover_malformed.csv")

    assert len(result.transactions) == 2
    assert len(result.failures) == 1
