"""Discover CSV parser.

Shares its header and row logic with Capital One (see
``_capone_discover_base.py``); differs only in ``institution_code``.
Descriptions may contain quoted commas, which ``csv.DictReader``
(used via the base parser's ``csv.reader``) handles natively.
"""
from __future__ import annotations

from app.parsers._capone_discover_base import CapOneDiscoverBaseParser


class DiscoverParser(CapOneDiscoverBaseParser):
    institution_code = "discover"
