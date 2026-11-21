from __future__ import annotations

import pytest

from app.parsers.amex import AmexParser
from app.parsers.capital_one import CapitalOneParser
from app.parsers.citi import CitiParser
from app.parsers.discover import DiscoverParser
from app.parsers.registry import (
    AmbiguousDetection,
    DetectionResult,
    UnknownFormatError,
    detect,
    get_parser,
    has_csv_extension,
)
from app.parsers.schwab import SchwabParser
from app.parsers.wells_fargo import WellsFargoParser


def test_detects_amex() -> None:
    result = detect(AmexParser.expected_header, "amex_90_day.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is AmexParser


def test_detects_citi() -> None:
    result = detect(CitiParser.expected_header, "citi_since_sept.CSV")
    assert isinstance(result, DetectionResult)
    assert result.parser is CitiParser


def test_detects_schwab() -> None:
    result = detect(SchwabParser.expected_header, "schwab_since_sept.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is SchwabParser


def test_detects_wells_fargo() -> None:
    result = detect(WellsFargoParser.expected_header, "wells_fargo_since_sept.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is WellsFargoParser


def test_wells_fargo_header_is_unambiguous() -> None:
    """Wells Fargo's all-caps header is unique, so detection never needs
    a filename tiebreak — any filename resolves it."""
    result = detect(WellsFargoParser.expected_header, "download.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is WellsFargoParser


def test_get_parser_by_wells_fargo_code() -> None:
    assert get_parser("wells_fargo") is WellsFargoParser


def test_capital_one_filename_tiebreak() -> None:
    result = detect(CapitalOneParser.expected_header, "capital_one_since_sept.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is CapitalOneParser


def test_discover_filename_tiebreak() -> None:
    result = detect(DiscoverParser.expected_header, "discover_since_sept.csv")
    assert isinstance(result, DetectionResult)
    assert result.parser is DiscoverParser


def test_ambiguous_when_filename_does_not_disambiguate() -> None:
    result = detect(CapitalOneParser.expected_header, "export.csv")
    assert isinstance(result, AmbiguousDetection)
    assert set(result.candidates) == {"capital_one", "discover"}


def test_unknown_header_raises() -> None:
    with pytest.raises(UnknownFormatError) as exc_info:
        detect(("Foo", "Bar"), "mystery.csv")
    assert exc_info.value.header == ("Foo", "Bar")


def test_get_parser_by_code() -> None:
    assert get_parser("amex") is AmexParser
    assert get_parser("capital_one") is CapitalOneParser
    assert get_parser("discover") is DiscoverParser
    assert get_parser("citi") is CitiParser
    assert get_parser("schwab") is SchwabParser


def test_get_parser_unknown_code_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        get_parser("not_a_bank")


def test_has_csv_extension_is_case_insensitive() -> None:
    assert has_csv_extension("foo.csv")
    assert has_csv_extension("foo.CSV")
    assert has_csv_extension("foo.Csv")
    assert not has_csv_extension("foo.txt")
    assert not has_csv_extension("foo.csv.txt")
