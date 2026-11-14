"""Ingest orchestration: validate -> detect -> parse -> persist.

This is the only layer that touches both the pure parsing code
(``app.parsers``) and the database. It is responsible for:

- Extension + header-based institution detection (explicit ``institution``
  always wins over auto-detection).
- Get-or-create of the ``Account`` row(s) — a single CSV can contain
  multiple distinct ``account_hint`` values (e.g. Amex's two cards, or
  Capital One's two card numbers in one export), so accounts are
  resolved per-row, not once per file.
- Idempotent bulk insert of transactions via
  ``INSERT ... ON CONFLICT (content_hash, occurrence_index) DO NOTHING``.
- Persisting isolated row failures as ``ParseFailure`` rows.
- Batch status/counts bookkeeping, with errors never swallowed into a
  200: any exception during the rows+batch transaction rolls it back
  and re-raises after marking the batch ``failed`` in a *separate*
  transaction.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain import ParsedTransaction
from app.models import Account, IngestBatch, Institution, ParseFailure, Transaction
from app.parsers.base import BaseParser
from app.parsers.registry import (
    AmbiguousDetection,
    DetectionResult,
    UnknownFormatError,
    detect,
    get_parser,
    has_csv_extension,
)
from app.services.cache import bump_generation
from app.services.categorizer import Categorizer
from app.services.hashing import assign_occurrence_indices, content_hash


class InvalidFileExtensionError(Exception):
    """Raised when the uploaded filename doesn't end in ``.csv`` (case-insensitive)."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(f"Unsupported file extension: {filename!r}")


class AmbiguousInstitutionError(Exception):
    """Raised when header-based detection can't disambiguate the
    institution and no explicit ``institution`` was supplied.

    Carries the candidate institution codes so the API layer can
    surface a 409 with a picker.
    """

    def __init__(self, candidates: tuple[str, ...]) -> None:
        self.candidates = candidates
        super().__init__(f"Ambiguous institution: candidates={candidates!r}")


class UnknownInstitutionCodeError(Exception):
    """Raised when an explicit ``institution`` form field doesn't match
    any known parser's institution_code."""

    def __init__(self, institution: str) -> None:
        self.institution = institution
        super().__init__(f"Unknown institution code: {institution!r}")


def _account_display_name(institution_display_name: str, account_hint: str, kind: str) -> str:
    """Build a human-friendly default display name for a newly
    discovered account, e.g. ``"Amex ···21003"`` for a card, or
    ``"Charles Schwab Checking"`` for a checking account.

    Some single-account card issuers (Citi) don't expose a card-number
    fragment in their export at all, so their parser uses the literal
    institution code as the account_hint (e.g. "citi"). In that case
    the hint itself is redundant with the institution name, so it's
    dropped from the display name rather than rendered as "···citi".
    """
    if kind == "checking":
        return f"{institution_display_name} Checking"
    if account_hint.isdigit() or (account_hint and not account_hint.isalpha()):
        return f"{institution_display_name} ···{account_hint}"
    return institution_display_name


@dataclass(frozen=True, slots=True)
class IngestOutcome:
    """Everything the API layer needs to build the upload response."""

    batch: IngestBatch
    failures: list[ParseFailure]


def _resolve_parser(
    header: tuple[str, ...], filename: str, institution: str | None
) -> type[BaseParser]:
    """Resolve which parser class to use for this upload.

    An explicit ``institution`` always wins, bypassing auto-detection
    entirely (this is also the retry path after a 409 ambiguity
    response). Otherwise falls back to header/filename detection.

    Raises ``UnknownInstitutionCodeError``, ``AmbiguousInstitutionError``,
    or lets ``UnknownFormatError`` propagate from ``detect``.
    """
    if institution is not None:
        try:
            return get_parser(institution)
        except KeyError:
            raise UnknownInstitutionCodeError(institution) from None

    detection = detect(header, filename)
    if isinstance(detection, AmbiguousDetection):
        raise AmbiguousInstitutionError(detection.candidates)
    assert isinstance(detection, DetectionResult)
    return detection.parser


def _sniff_header(text: str) -> tuple[str, ...]:
    """Read just the header row from CSV text (first non-empty line,
    split via the stdlib csv reader so quoting is respected)."""
    import csv
    import io

    reader = csv.reader(io.StringIO(text))
    try:
        header_row = next(reader)
    except StopIteration:
        return ()
    return tuple(h.strip() for h in header_row)


def _get_or_create_account(
    db: Session,
    institution: Institution,
    account_hint: str,
    kind: str,
) -> Account:
    """Get-or-create the Account row for (institution, account_hint).

    Flushes so the new row has an id available for FK use within the
    same transaction, without committing.
    """
    existing = db.execute(
        select(Account).where(
            Account.institution_id == institution.id,
            Account.account_hint == account_hint,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    account = Account(
        institution_id=institution.id,
        account_hint=account_hint,
        display_name=_account_display_name(institution.display_name, account_hint, kind),
        kind=kind,
    )
    db.add(account)
    db.flush()
    return account


def ingest_file(
    db: Session,
    *,
    filename: str,
    file_bytes: bytes,
    institution: str | None = None,
) -> IngestOutcome:
    """Run the full ingest pipeline for one uploaded CSV file.

    Raises (never caught here, so callers/API layer map these to HTTP):
    - ``InvalidFileExtensionError`` — bad extension.
    - ``UnknownInstitutionCodeError`` — explicit institution not recognized.
    - ``AmbiguousInstitutionError`` — ambiguous auto-detection, candidates attached.
    - ``app.parsers.registry.UnknownFormatError`` — header matches no parser.

    Any other exception raised while building/inserting rows aborts the
    rows+batch transaction (rolled back), then marks the batch (if it
    was already flushed with an id) ``failed`` in a separate
    transaction, and re-raises — a DB failure is never swallowed into a
    200 response.
    """
    if not has_csv_extension(filename):
        raise InvalidFileExtensionError(filename)

    text = file_bytes.decode("utf-8-sig")
    header = _sniff_header(text)

    parser = _resolve_parser(header, filename, institution)
    # UnknownFormatError propagates from here if institution was None
    # and detect() couldn't match any parser at all.

    parse_result = parser.parse(text, filename)

    institution_row = db.execute(
        select(Institution).where(Institution.code == parser.institution_code)
    ).scalar_one()

    file_sha256 = hashlib.sha256(file_bytes).hexdigest()

    batch = IngestBatch(
        filename=filename,
        institution_id=institution_row.id,
        account_id=None,  # may span multiple accounts; set below if exactly one
        file_sha256=file_sha256,
        row_count=len(parse_result.transactions) + len(parse_result.failures),
        status="pending",
    )
    db.add(batch)
    db.flush()  # assign batch.id

    try:
        categorizer = Categorizer.load(db)

        account_cache: dict[str, Account] = {}

        def _account_for(hint: str) -> Account:
            cached = account_cache.get(hint)
            if cached is not None:
                return cached
            acct = _get_or_create_account(db, institution_row, hint, parser.account_kind)
            account_cache[hint] = acct
            return acct

        indexed: list[tuple[ParsedTransaction, int]] = assign_occurrence_indices(
            parse_result.transactions, parser.institution_code
        )

        inserted_count = 0
        duplicate_count = 0

        for txn, occurrence_index in indexed:
            account = _account_for(txn.account_hint)
            categorization = categorizer.categorize(txn.normalized_description)
            h = content_hash(
                institution_code=parser.institution_code,
                account_hint=txn.account_hint,
                txn_date=txn.txn_date,
                amount=txn.amount,
                normalized_description=txn.normalized_description,
            )

            stmt = (
                pg_insert(Transaction)
                .values(
                    account_id=account.id,
                    batch_id=batch.id,
                    txn_date=txn.txn_date,
                    posted_date=txn.posted_date,
                    description=txn.description,
                    normalized_description=txn.normalized_description,
                    amount=txn.amount,
                    bank_category=txn.bank_category,
                    category_id=categorization.category_id,
                    category_source=categorization.source,
                    content_hash=h,
                    occurrence_index=occurrence_index,
                    raw_row=txn.raw_row,
                )
                .on_conflict_do_nothing(
                    index_elements=["content_hash", "occurrence_index"]
                )
                .returning(Transaction.id)
            )
            result = db.execute(stmt)
            if result.first() is not None:
                inserted_count += 1
            else:
                duplicate_count += 1

        failure_rows: list[ParseFailure] = []
        for failure in parse_result.failures:
            failure_row = ParseFailure(
                batch_id=batch.id,
                line_number=failure.line_number,
                raw_line=failure.raw_line,
                error_type=failure.error_type,
                error_message=failure.error_message,
            )
            db.add(failure_row)
            failure_rows.append(failure_row)

        # Single-account convenience pointer on the batch (most uploads
        # are single-account); leave null when a file spans >1 account.
        if len(account_cache) == 1:
            batch.account_id = next(iter(account_cache.values())).id

        batch.inserted_count = inserted_count
        batch.duplicate_count = duplicate_count
        batch.failure_count = len(failure_rows)
        batch.status = "completed_with_errors" if failure_rows else "completed"

        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        _mark_batch_failed(db, batch.id)
        raise

    bump_generation()
    db.refresh(batch)
    return IngestOutcome(batch=batch, failures=list(batch.failures))


def _mark_batch_failed(db: Session, batch_id: int) -> None:
    """Mark a batch ``failed`` in its own fresh transaction, after the
    rows+batch transaction has already been rolled back. Best-effort:
    if even this update fails (e.g. the DB connection itself is down),
    we let that exception propagate too rather than hide it."""
    batch = db.get(IngestBatch, batch_id)
    if batch is None:
        return
    batch.status = "failed"
    db.commit()
