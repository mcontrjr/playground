"""Wells Fargo checking CSV parser.

Format quirks:
- All fields are quoted; header is ALL CAPS
  (``DATE,DESCRIPTION,AMOUNT,CHECK #,STATUS``).
- Date format MM/DD/YYYY, no separate posted date.
- A single signed ``AMOUNT`` column that already matches our own
  convention (negative = money out, positive = money in), so the parsed
  sign is kept as-is rather than derived from debit/credit columns the
  way Citi and Schwab do.
- Descriptions carry long runs of internal whitespace used as column
  padding in the source statement (e.g. ``ATM CASH DEPOSIT        ON``).
  The raw text is preserved verbatim in ``description``; the collapsed
  form lives in ``normalized_description``, as with every other parser.
- ``STATUS`` is ``Posted`` or ``Pending``. Pending rows are skipped
  (``parse_row`` returns ``None``): their amount and date can still
  change before posting, which would re-hash into a second, duplicate
  transaction once the final version is exported.
- ``CHECK #`` is empty on every row of the real export, but is part of
  the header and is preserved in ``raw_row``.
- No account column at all; account hint is the fixed string
  "wells_fargo" (the same approach CitiParser takes).
"""
from __future__ import annotations

from app.domain import ParsedTransaction
from app.parsers.base import BaseParser, normalize_description, parse_date, parse_money

_DATE_FMT = "%m/%d/%Y"
_PENDING_STATUS = "pending"


class WellsFargoParser(BaseParser):
    institution_code = "wells_fargo"
    account_kind = "checking"
    expected_header = ("DATE", "DESCRIPTION", "AMOUNT", "CHECK #", "STATUS")

    @classmethod
    def parse_row(cls, row: dict[str, str], line_no: int) -> ParsedTransaction | None:
        # Skip not-yet-final rows before any other work: a pending row's
        # amount/date may change before it posts.
        if row.get("STATUS", "").strip().lower() == _PENDING_STATUS:
            return None

        txn_date = parse_date(row["DATE"], _DATE_FMT)
        description = row["DESCRIPTION"].strip()

        amount_raw = row.get("AMOUNT", "").strip()
        if not amount_raw:
            raise ValueError("row has no AMOUNT value")

        # Wells Fargo's sign convention already matches ours.
        amount = parse_money(amount_raw)

        return ParsedTransaction(
            txn_date=txn_date,
            posted_date=None,
            description=description,
            normalized_description=normalize_description(description),
            amount=amount,
            account_hint="wells_fargo",
            bank_category=None,
            raw_row=dict(row),
            line_number=line_no,
        )
