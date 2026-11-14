"""Parser detection and lookup.

Detection is header-based. Capital One and Discover share an identical
header, so when both match, the filename is used as a tiebreak; if the
filename doesn't disambiguate either, an ``AmbiguousDetection`` result
is returned for the caller (Phase 3's upload API) to turn into a 409
with an explicit-institution retry path.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.parsers.amex import AmexParser
from app.parsers.base import BaseParser
from app.parsers.capital_one import CapitalOneParser
from app.parsers.citi import CitiParser
from app.parsers.discover import DiscoverParser
from app.parsers.schwab import SchwabParser

_PARSERS: tuple[type[BaseParser], ...] = (
    AmexParser,
    CapitalOneParser,
    DiscoverParser,
    CitiParser,
    SchwabParser,
)

_PARSERS_BY_CODE: dict[str, type[BaseParser]] = {p.institution_code: p for p in _PARSERS}

# Filename substrings (checked case-insensitively) that disambiguate
# Capital One vs. Discover when their identical headers both match.
_CAPITAL_ONE_FILENAME_HINTS: tuple[str, ...] = ("capital", "cap_one", "capitalone")
_DISCOVER_FILENAME_HINTS: tuple[str, ...] = ("discover",)


class UnknownFormatError(Exception):
    """Raised when a CSV header doesn't match any known parser."""

    def __init__(self, header: tuple[str, ...]) -> None:
        self.header = header
        super().__init__(f"Unrecognized CSV header: {header!r}")


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """A single, unambiguous parser match."""

    parser: type[BaseParser]


@dataclass(frozen=True, slots=True)
class AmbiguousDetection:
    """Multiple parsers match the header and the filename didn't
    disambiguate. Carries the candidate institution codes so the
    caller (the upload API) can surface a 409 with a picker."""

    candidates: tuple[str, ...] = field(default_factory=tuple)


def has_csv_extension(filename: str) -> bool:
    """Case-insensitive ``.csv`` extension check (Citi ships `.CSV`)."""
    return filename.lower().endswith(".csv")


def detect(header: tuple[str, ...], filename: str) -> DetectionResult | AmbiguousDetection:
    """Detect which parser should handle a file based on its header,
    using the filename only to break the Capital One/Discover tie.

    Raises ``UnknownFormatError`` if no parser's expected header
    matches at all.
    """
    matches = [p for p in _PARSERS if p.matches_header(header)]

    if not matches:
        raise UnknownFormatError(header)

    if len(matches) == 1:
        return DetectionResult(parser=matches[0])

    # More than one match today only happens for CapOne/Discover, since
    # their headers are identical by design. Try filename-based tiebreak.
    codes = {p.institution_code for p in matches}
    if codes == {"capital_one", "discover"}:
        lowered = filename.lower()
        is_capone = any(hint in lowered for hint in _CAPITAL_ONE_FILENAME_HINTS)
        is_discover = any(hint in lowered for hint in _DISCOVER_FILENAME_HINTS)

        if is_capone and not is_discover:
            return DetectionResult(parser=_PARSERS_BY_CODE["capital_one"])
        if is_discover and not is_capone:
            return DetectionResult(parser=_PARSERS_BY_CODE["discover"])

    return AmbiguousDetection(candidates=tuple(sorted(codes)))


def get_parser(institution_code: str) -> type[BaseParser]:
    """Look up a parser class by institution code.

    Raises ``KeyError`` if the code is unknown.
    """
    return _PARSERS_BY_CODE[institution_code]
