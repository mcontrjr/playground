"""Shared pytest fixtures: paths to fixture CSVs and the real sample files."""
from __future__ import annotations

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
FIXTURES_CSV_DIR = TESTS_DIR / "fixtures" / "csv"
REPO_ROOT = TESTS_DIR.parent.parent
REAL_TRANSACTIONS_DIR = REPO_ROOT / "transactions"


@pytest.fixture
def fixtures_csv_dir() -> Path:
    """Directory containing hand-crafted small fixture CSVs."""
    return FIXTURES_CSV_DIR


@pytest.fixture
def real_transactions_dir() -> Path:
    """Directory containing the 5 real ground-truth sample CSVs."""
    return REAL_TRANSACTIONS_DIR


def fixture_path(name: str) -> Path:
    """Absolute path to a fixture CSV by filename."""
    return FIXTURES_CSV_DIR / name


def real_file_path(name: str) -> Path:
    """Absolute path to one of the 5 real ground-truth sample CSVs."""
    return REAL_TRANSACTIONS_DIR / name


def read_text(path: Path) -> str:
    """Read a fixture/real file as text (utf-8, no newline translation
    surprises — parsers operate on the raw text via csv.reader)."""
    return path.read_text(encoding="utf-8")
