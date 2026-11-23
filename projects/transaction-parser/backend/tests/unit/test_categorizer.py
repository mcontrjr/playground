"""Unit tests for the categorizer's matched_keyword reporting.

These exercise ``Categorizer`` directly against hand-built rules, so they
don't need a database or the seeded category set.
"""
from __future__ import annotations

from app.services.categorizer import Categorizer, _KeywordRule

TRANSFERS_ID = 1
FOOD_ID = 2
COSTCO_ID = 3
UNCATEGORIZED_ID = 99


def _categorizer() -> Categorizer:
    return Categorizer(
        transfer_rules=[_KeywordRule(keyword="ONLINE PAYMENT", category_id=TRANSFERS_ID)],
        general_rules=[
            # Longest-first within a category, as Categorizer.load builds it.
            _KeywordRule(keyword="COSTCO GAS", category_id=COSTCO_ID),
            _KeywordRule(keyword="CHIPOTLE", category_id=FOOD_ID),
        ],
        uncategorized_category_id=UNCATEGORIZED_ID,
    )


def test_keyword_match_reports_the_winning_keyword() -> None:
    result = _categorizer().categorize("CHIPOTLE 1521 BURBANK")

    assert result.category_id == FOOD_ID
    assert result.source == "keyword"
    assert result.matched_keyword == "CHIPOTLE"


def test_transfer_match_reports_the_winning_keyword() -> None:
    result = _categorizer().categorize("CITI CARD ONLINE PAYMENT 260910")

    assert result.category_id == TRANSFERS_ID
    assert result.source == "transfer"
    assert result.matched_keyword == "ONLINE PAYMENT"


def test_no_match_reports_no_keyword() -> None:
    """'default' means nothing matched, so there is no keyword to name —
    null here must read as 'nothing matched', never 'unknown'."""
    result = _categorizer().categorize("SOME UNRECOGNIZED MERCHANT")

    assert result.category_id == UNCATEGORIZED_ID
    assert result.source == "default"
    assert result.matched_keyword is None


def test_reported_keyword_is_the_one_that_actually_won() -> None:
    """When two categories both match, the recorded keyword must belong
    to the winner — not merely be any keyword present in the text."""
    result = _categorizer().categorize("COSTCO GAS #0677 BURBANK CA")

    assert result.category_id == COSTCO_ID
    assert result.matched_keyword == "COSTCO GAS"


def test_transfer_stage_wins_over_a_better_priority_keyword() -> None:
    """Transfer rules are scanned first, so they win even when a general
    rule would otherwise match — and the keyword recorded is the
    transfer one."""
    categorizer = Categorizer(
        transfer_rules=[_KeywordRule(keyword="PMT", category_id=TRANSFERS_ID)],
        general_rules=[_KeywordRule(keyword="AMAZON", category_id=FOOD_ID)],
        uncategorized_category_id=UNCATEGORIZED_ID,
    )

    result = categorizer.categorize("AMAZON MKTPLACE PMTS")

    assert result.category_id == TRANSFERS_ID
    assert result.source == "transfer"
    assert result.matched_keyword == "PMT"


def test_explain_winner_agrees_with_categorize() -> None:
    """The clash report's winner must always be the row categorize()
    actually returns, including the keyword behind it."""
    categorizer = _categorizer()
    description = "COSTCO GAS #0677 BURBANK CA"

    verdict = categorizer.categorize(description)
    report = categorizer.explain(description)

    assert report.winner is not None
    assert report.winner.category_id == verdict.category_id
    assert report.winner.keyword == verdict.matched_keyword
