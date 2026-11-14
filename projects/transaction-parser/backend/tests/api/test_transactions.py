"""API tests for GET /transactions (filters/sort/pagination/exclusion)
and PATCH /transactions/{id} (manual recategorize + stickiness)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Account, Category, Institution, Transaction


def _make_batch(db_session: Session, institution_code: str = "amex"):
    from app.models import IngestBatch

    institution = db_session.query(Institution).filter(Institution.code == institution_code).one()
    account = Account(institution_id=institution.id, account_hint="99999", display_name="Test Amex", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        filename="test.csv",
        institution_id=institution.id,
        account_id=account.id,
        file_sha256="0" * 64,
        row_count=0,
        status="completed",
    )
    db_session.add(batch)
    db_session.flush()
    return account, batch


def _make_txn(
    db_session: Session,
    account: Account,
    batch,
    *,
    txn_date: date,
    amount: str,
    description: str,
    category: Category | None,
    category_source: str = "default",
    content_hash_suffix: str = "a",
) -> Transaction:
    normalized = description.upper()
    txn = Transaction(
        account_id=account.id,
        batch_id=batch.id,
        txn_date=txn_date,
        posted_date=txn_date,
        description=description,
        normalized_description=normalized,
        amount=Decimal(amount),
        bank_category=None,
        category_id=category.id if category else None,
        category_source=category_source,
        content_hash=(content_hash_suffix * 64)[:64],
        occurrence_index=0,
        raw_row={"raw": description},
    )
    db_session.add(txn)
    db_session.flush()
    return txn


def _seeded_category(db_session: Session, name: str) -> Category:
    return db_session.query(Category).filter(Category.name == name).one()


def test_list_transactions_default_excludes_transfers(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    transfers = _seeded_category(db_session, "Payments & Transfers")
    food = _seeded_category(db_session, "FOOD")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-50.00",
        description="AUTOPAY PAYMENT THANK YOU", category=transfers, category_source="transfer",
        content_hash_suffix="1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 2), amount="-10.00",
        description="CHIPOTLE MEXICAN GRILL", category=food, category_source="keyword",
        content_hash_suffix="2",
    )
    db_session.commit()

    default_resp = client.get("/api/v1/transactions")
    assert default_resp.status_code == 200
    default_body = default_resp.json()
    assert default_body["total"] == 1
    assert all(item["category_name"] != "Payments & Transfers" for item in default_body["items"])

    included_resp = client.get("/api/v1/transactions", params={"include_excluded": "true"})
    included_body = included_resp.json()
    assert included_body["total"] == 2


def test_list_transactions_date_and_category_filters(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 9, 15), amount="-10.00",
        description="CHIPOTLE", category=food, category_source="keyword", content_hash_suffix="3",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 15), amount="-20.00",
        description="CHEVRON GAS STATION", category=gas, category_source="keyword", content_hash_suffix="4",
    )
    db_session.commit()

    date_resp = client.get(
        "/api/v1/transactions",
        params={"date_from": "2026-10-01", "date_to": "2026-10-31", "include_excluded": "true"},
    )
    assert date_resp.json()["total"] == 1
    assert date_resp.json()["items"][0]["description"] == "CHEVRON GAS STATION"

    category_resp = client.get(
        "/api/v1/transactions",
        params={"category_ids": [food.id], "include_excluded": "true"},
    )
    assert category_resp.json()["total"] == 1
    assert category_resp.json()["items"][0]["description"] == "CHIPOTLE"


def test_list_transactions_q_search_case_insensitive(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-10.00",
        description="Starbucks Coffee Shop", category=food, category_source="keyword", content_hash_suffix="5",
    )
    db_session.commit()

    resp = client.get("/api/v1/transactions", params={"q": "starbucks", "include_excluded": "true"})
    assert resp.json()["total"] == 1

    miss_resp = client.get("/api/v1/transactions", params={"q": "nonexistent_merchant", "include_excluded": "true"})
    assert miss_resp.json()["total"] == 0


def test_list_transactions_sort_and_pagination(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")

    for i in range(5):
        _make_txn(
            db_session, account, batch, txn_date=date(2026, 10, 1 + i), amount=f"-{10 + i}.00",
            description=f"MERCHANT {i}", category=food, category_source="keyword",
            content_hash_suffix=str(i),
        )
    db_session.commit()

    page1 = client.get(
        "/api/v1/transactions",
        params={"sort": "txn_date", "order": "asc", "limit": 2, "offset": 0, "include_excluded": "true"},
    )
    body1 = page1.json()
    assert body1["total"] == 5
    assert len(body1["items"]) == 2
    assert body1["items"][0]["txn_date"] == "2026-10-01"

    page2 = client.get(
        "/api/v1/transactions",
        params={"sort": "txn_date", "order": "asc", "limit": 2, "offset": 2, "include_excluded": "true"},
    )
    body2 = page2.json()
    assert body2["items"][0]["txn_date"] == "2026-10-03"

    amount_sorted = client.get(
        "/api/v1/transactions",
        params={"sort": "amount", "order": "asc", "include_excluded": "true"},
    )
    amounts = [item["amount"] for item in amount_sorted.json()["items"]]
    assert amounts == sorted(amounts, key=lambda a: Decimal(a))


def test_patch_transaction_manual_recategorize(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    txn = _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-10.00",
        description="AMBIGUOUS MERCHANT", category=food, category_source="keyword",
        content_hash_suffix="6",
    )
    db_session.commit()

    resp = client.patch(f"/api/v1/transactions/{txn.id}", json={"category_id": gas.id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category_id"] == gas.id
    assert body["category_source"] == "manual"


def test_patch_transaction_404(client: TestClient) -> None:
    resp = client.patch("/api/v1/transactions/999999", json={"category_id": 1})
    assert resp.status_code == 404


def test_manual_recategorize_sticky_against_apply_to_existing(
    client: TestClient, db_session: Session
) -> None:
    """A manually recategorized transaction must NOT be moved by a
    subsequent keyword add_keyword(apply_to_existing=True) call, even
    if the new keyword would otherwise match its description."""
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    uncategorized = _seeded_category(db_session, "Uncategorized")

    txn = _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-10.00",
        description="PEETS COFFEE SHOP", category=uncategorized, category_source="default",
        content_hash_suffix="7",
    )
    db_session.commit()

    # Manually recategorize it to Gas (nonsensical, but proves stickiness).
    gas = _seeded_category(db_session, "GAS")
    patch_resp = client.patch(f"/api/v1/transactions/{txn.id}", json={"category_id": gas.id})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["category_source"] == "manual"

    # Now add a keyword to Food that matches this description, with apply_to_existing.
    add_resp = client.post(
        f"/api/v1/categories/{food.id}/keywords",
        json={"keyword": "PEETS COFFEE", "apply_to_existing": True},
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["applied_count"] == 0

    db_session.refresh(txn)
    assert txn.category_id == gas.id
    assert txn.category_source == "manual"
