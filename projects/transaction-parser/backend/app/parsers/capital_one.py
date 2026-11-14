"""Capital One CSV parser.

Shares its header and row logic with Discover (see
``_capone_discover_base.py``); differs only in ``institution_code``.
Disambiguation between the two when the filename doesn't help is
handled by ``registry.py``.
"""
from __future__ import annotations

from app.parsers._capone_discover_base import CapOneDiscoverBaseParser


class CapitalOneParser(CapOneDiscoverBaseParser):
    institution_code = "capital_one"
