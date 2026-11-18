"""API tests for budget expense CRUD and the month-scoped summary."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Account, Category, Institution, IngestBatch, Transaction


def _make_batch(db_session: Session, institution_code: str = "amex"):
    institution = db_session.query(Institution).filter(Institution.code == institution_code).one()
    account = Account(institution_id=institution.id, account_hint="88888", display_name="Test Account", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        filename="test.csv",
        institution_id=institution.id,
        account_id=account.id,
        file_sha256="1" * 64,
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
    description: str,
    category: Category | None,
    txn_date: date = date(2026, 11, 5),
    content_hash_suffix: str = "a",
    amount: str = "-10.00",
) -> Transaction:
    txn = Transaction(
        account_id=account.id,
        batch_id=batch.id,
        txn_date=txn_date,
        posted_date=txn_date,
        description=description,
        normalized_description=description.upper(),
        amount=Decimal(amount),
        bank_category=None,
        category_id=category.id if category else None,
        category_source="default",
        content_hash=(content_hash_suffix * 64)[:64],
        occurrence_index=0,
        raw_row={"raw": description},
    )
    db_session.add(txn)
    db_session.flush()
    return txn


def _seeded_category(db_session: Session, name: str) -> Category:
    return db_session.query(Category).filter(Category.name == name).one()


def test_create_expense_links_categories(client: TestClient, db_session: Session) -> None:
    groceries = _seeded_category(db_session, "GROCERIES")
    db_session.commit()

    resp = client.post(
        "/api/v1/budget?month=2026-11",
        json={"name": "GROCERIES", "goal_amount": "600.00", "category_ids": [groceries.id]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "GROCERIES"
    assert body["goal_amount"] == "600.00"
    assert [c["id"] for c in body["categories"]] == [groceries.id]
    assert body["actual_amount"] == "0.00"


def test_summary_computes_actual_from_linked_category_transactions(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    groceries = _seeded_category(db_session, "GROCERIES")
    income = _seeded_category(db_session, "Income")

    _make_txn(db_session, account, batch, description="TRADER JOE", category=groceries, amount="-45.00", content_hash_suffix="1")
    _make_txn(db_session, account, batch, description="SPROUTS", category=groceries, amount="-30.00", content_hash_suffix="2")
    # Outside November — should not count toward the November actual.
    _make_txn(
        db_session, account, batch, description="TRADER JOE", category=groceries,
        amount="-99.00", txn_date=date(2026, 10, 15), content_hash_suffix="3",
    )
    _make_txn(db_session, account, batch, description="PAYROLL", category=income, amount="3000.00", content_hash_suffix="4")
    db_session.commit()

    create_resp = client.post(
        "/api/v1/budget?month=2026-11",
        json={"name": "GROCERIES", "goal_amount": "200.00", "category_ids": [groceries.id]},
    )
    assert create_resp.status_code == 201

    resp = client.get("/api/v1/budget/summary?month=2026-11")
    assert resp.status_code == 200
    body = resp.json()
    assert body["month"] == "2026-11"
    assert body["income"] == "3000.00"
    assert len(body["expenses"]) == 1
    expense = body["expenses"][0]
    assert expense["name"] == "GROCERIES"
    assert expense["actual_amount"] == "75.00"
    assert body["total_goal"] == "200.00"
    assert body["total_actual"] == "75.00"


def test_patch_expense_replaces_category_links(client: TestClient, db_session: Session) -> None:
    groceries = _seeded_category(db_session, "GROCERIES")
    gas = _seeded_category(db_session, "GAS")
    db_session.commit()

    create_resp = client.post(
        "/api/v1/budget?month=2026-11",
        json={"name": "Essentials", "category_ids": [groceries.id]},
    )
    expense_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/budget/{expense_id}?month=2026-11",
        json={"category_ids": [gas.id]},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert [c["id"] for c in body["categories"]] == [gas.id]


def test_delete_expense(client: TestClient, db_session: Session) -> None:
    create_resp = client.post("/api/v1/budget?month=2026-11", json={"name": "Rent", "category_ids": []})
    expense_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/budget/{expense_id}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted_budget_expense_id": expense_id}

    summary = client.get("/api/v1/budget/summary?month=2026-11")
    assert summary.json()["expenses"] == []


def test_create_expense_rejects_unknown_category(client: TestClient) -> None:
    resp = client.post("/api/v1/budget?month=2026-11", json={"name": "Bogus", "category_ids": [999999]})
    assert resp.status_code == 404
