"""API tests for the upload/ingest pipeline, run against a real Postgres
test database (see conftest.py). Covers: real-file ingestion counts,
re-upload idempotency, the Capital One/Discover ambiguity 409 -> retry
flow, malformed-row isolation surfaced via /failures, transfer
categorization, and multi-account creation from a single file.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TRANSACTIONS_DIR = REPO_ROOT / "transactions"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "csv"

REAL_FILES_AND_EXPECTED_COUNTS = [
    ("amex_90_day.csv", 105),
    ("capital_one_since_sept.csv", 122),
    ("discover_since_sept.csv", 61),
    ("citi_since_sept.CSV", 93),
    ("schwab_since_sept.csv", 67),
]


def _upload(client: TestClient, path: Path, institution: str | None = None) -> dict:
    data = {}
    if institution is not None:
        data["institution"] = institution
    with path.open("rb") as f:
        files = {"file": (path.name, f, "text/csv")}
        resp = client.post("/api/v1/uploads", files=files, data=data)
    return resp


def test_upload_each_real_csv_zero_failures(client: TestClient) -> None:
    for filename, expected_inserted in REAL_FILES_AND_EXPECTED_COUNTS:
        path = TRANSACTIONS_DIR / filename
        institution = "capital_one" if filename.startswith("capital_one") else None
        resp = _upload(client, path, institution=institution)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["counts"]["inserted"] == expected_inserted, (filename, body)
        assert body["counts"]["duplicates"] == 0, (filename, body)
        assert body["counts"]["failures"] == 0, (filename, body)
        assert body["status"] == "completed"


def test_reupload_same_file_is_all_duplicates(client: TestClient) -> None:
    path = TRANSACTIONS_DIR / "amex_90_day.csv"

    first = _upload(client, path)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["counts"]["inserted"] == 105
    assert first_body["counts"]["duplicates"] == 0

    second = _upload(client, path)
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["counts"]["inserted"] == 0
    assert second_body["counts"]["duplicates"] == 105
    assert second_body["counts"]["failures"] == 0


def test_reupload_creates_no_new_transaction_rows(client: TestClient, db_session: Session) -> None:
    from app.models import Transaction

    path = TRANSACTIONS_DIR / "amex_90_day.csv"
    _upload(client, path)
    count_after_first = db_session.query(Transaction).count()

    _upload(client, path)
    count_after_second = db_session.query(Transaction).count()

    assert count_after_first == 105
    assert count_after_second == count_after_first


def test_ambiguous_institution_409_then_retry_succeeds(client: TestClient) -> None:
    # export.csv has capital_one-shaped content but a filename that
    # doesn't disambiguate capital_one vs. discover.
    ambiguous_path = FIXTURES_DIR / "export.csv"

    resp = _upload(client, ambiguous_path)
    assert resp.status_code == 409, resp.text
    body = resp.json()
    detail = body["detail"]
    assert detail["code"] == "AMBIGUOUS_INSTITUTION"
    assert set(detail["candidates"]) == {"capital_one", "discover"}

    retry = _upload(client, ambiguous_path, institution="capital_one")
    assert retry.status_code == 201, retry.text
    retry_body = retry.json()
    assert retry_body["institution"] == "capital_one"
    assert retry_body["counts"]["failures"] == 0
    assert retry_body["counts"]["inserted"] > 0


def test_malformed_fixture_completes_with_errors_and_failure_is_resolvable(
    client: TestClient,
) -> None:
    path = FIXTURES_DIR / "schwab_malformed.csv"

    resp = _upload(client, path)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed_with_errors"
    assert body["counts"]["failures"] >= 1
    assert len(body["failures"]) >= 1

    failures_resp = client.get("/api/v1/failures", params={"resolved": "false"})
    assert failures_resp.status_code == 200
    failures = failures_resp.json()
    assert len(failures) >= 1
    failure_id = failures[0]["id"]
    assert failures[0]["resolved"] is False

    patch_resp = client.patch(f"/api/v1/failures/{failure_id}", json={"resolved": True})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["resolved"] is True

    unresolved_resp = client.get("/api/v1/failures", params={"resolved": "false"})
    unresolved_ids = {f["id"] for f in unresolved_resp.json()}
    assert failure_id not in unresolved_ids


def test_transfer_categorization_amex_and_schwab(client: TestClient, db_session: Session) -> None:
    from app.models import Category, Transaction

    _upload(client, TRANSACTIONS_DIR / "amex_90_day.csv")
    _upload(client, TRANSACTIONS_DIR / "schwab_since_sept.csv")

    transfers_category = (
        db_session.query(Category).filter(Category.name == "Payments & Transfers").one()
    )

    amex_autopay = (
        db_session.query(Transaction)
        .filter(Transaction.normalized_description.like("%AUTOPAY PAYMENT - THANK YOU%"))
        .all()
    )
    assert amex_autopay, "expected at least one Amex AUTOPAY row"
    for txn in amex_autopay:
        assert txn.category_id == transfers_category.id
        assert txn.category_source == "transfer"

    schwab_card_payments = (
        db_session.query(Transaction)
        .filter(Transaction.normalized_description.like("%CARD ONLINE PAYMENT%"))
        .all()
    )
    assert schwab_card_payments, "expected at least one Schwab card-payment row"
    for txn in schwab_card_payments:
        assert txn.category_id == transfers_category.id
        assert txn.category_source == "transfer"


def test_amex_multi_account_creates_two_accounts(client: TestClient, db_session: Session) -> None:
    from app.models import Account, Institution

    _upload(client, TRANSACTIONS_DIR / "amex_90_day.csv")

    amex = db_session.query(Institution).filter(Institution.code == "amex").one()
    accounts = db_session.query(Account).filter(Account.institution_id == amex.id).all()

    assert len(accounts) == 2
    hints = {a.account_hint for a in accounts}
    assert hints == {"21003", "21029"}
    for account in accounts:
        assert account.kind == "card"


def test_upload_batch_list_and_detail(client: TestClient) -> None:
    upload_resp = _upload(client, TRANSACTIONS_DIR / "discover_since_sept.csv")
    assert upload_resp.status_code == 201
    batch_id = upload_resp.json()["id"]

    list_resp = client.get("/api/v1/uploads")
    assert list_resp.status_code == 200
    batches = list_resp.json()
    assert any(b["id"] == batch_id for b in batches)

    detail_resp = client.get(f"/api/v1/uploads/{batch_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == batch_id
    assert "failures" in detail


def test_bad_extension_rejected_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/uploads",
        files={"file": ("statement.txt", b"Date,Amount\n1/1/2026,1.00\n", "text/plain")},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_EXTENSION"


def test_unknown_header_rejected_422_and_echoes_header(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/uploads",
        files={"file": ("mystery.csv", b"Foo,Bar,Baz\n1,2,3\n", "text/csv")},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "UNKNOWN_FORMAT"
    assert detail["header"] == ["Foo", "Bar", "Baz"]
