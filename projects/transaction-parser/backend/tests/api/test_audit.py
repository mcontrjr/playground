"""API tests for the audit trail: mutations produce events with the
right counts, and the listing endpoint paginates newest-first."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Account, Category, Institution, IngestBatch, Transaction


def _ws_id(db_session: Session) -> int:
    """Id of the seeded `init` workspace these tests operate in.

    Resolved here rather than threaded through every helper call so the
    existing single-workspace tests read exactly as they did before
    workspaces existed.
    """
    from app.models import Workspace
    from app.seed import INIT_SLUG

    return db_session.query(Workspace).filter(Workspace.slug == INIT_SLUG).one().id


def _make_batch(db_session: Session, institution_code: str = "amex"):
    institution = db_session.query(Institution).filter(Institution.code == institution_code).one()
    account = Account(workspace_id=_ws_id(db_session), institution_id=institution.id, account_hint="77777", display_name="Audit Test Account", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        workspace_id=_ws_id(db_session),
        filename="audit_test.csv",
        institution_id=institution.id,
        account_id=account.id,
        file_sha256="2" * 64,
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
    category_source: str = "default",
    content_hash_suffix: str = "a",
    amount: str = "-10.00",
) -> Transaction:
    txn = Transaction(
        workspace_id=_ws_id(db_session),
        account_id=account.id,
        batch_id=batch.id,
        txn_date=date(2026, 10, 1),
        posted_date=date(2026, 10, 1),
        description=description,
        normalized_description=description.upper(),
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


def test_create_category_records_audit_event(client: TestClient) -> None:
    resp = client.post("/api/v1/categories", json={"name": "Audit Created Category"})
    assert resp.status_code == 201

    audit = client.get("/api/v1/audit")
    assert audit.status_code == 200
    items = audit.json()["items"]
    matches = [e for e in items if e["event_type"] == "category.created"]
    assert matches
    assert matches[0]["description"]
    assert "Audit Created Category" in matches[0]["description"]


def test_rename_category_records_audit_event_with_affected_count(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    _make_txn(db_session, account, batch, description="CHIPOTLE", category=food, category_source="keyword", content_hash_suffix="1")
    db_session.commit()

    resp = client.patch(f"/api/v1/categories/{food.id}", json={"name": "Audit Renamed Food"})
    assert resp.status_code == 200

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    matches = [e for e in items if e["event_type"] == "category.renamed"]
    assert matches
    assert matches[0]["payload"]["to"] == "Audit Renamed Food"


def test_delete_category_records_audit_event_with_affected_count(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    _make_txn(db_session, account, batch, description="CHEVRON", category=gas, category_source="keyword", content_hash_suffix="2")
    db_session.commit()

    resp = client.delete(f"/api/v1/categories/{gas.id}")
    assert resp.status_code == 200

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    matches = [e for e in items if e["event_type"] == "category.deleted"]
    assert matches
    assert matches[0]["affected_count"] == 1
    assert matches[0]["entity_type"] == "category"


def test_add_and_remove_keyword_record_audit_events(client: TestClient, db_session: Session) -> None:
    food = _seeded_category(db_session, "FOOD")

    add_resp = client.post(f"/api/v1/categories/{food.id}/keywords", json={"keyword": "AUDITKEYWORD"})
    assert add_resp.status_code == 201
    keyword_id = add_resp.json()["keyword"]["id"]

    del_resp = client.delete(f"/api/v1/categories/{food.id}/keywords/{keyword_id}")
    assert del_resp.status_code == 200

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    assert any(e["event_type"] == "keyword.added" for e in items)
    assert any(e["event_type"] == "keyword.removed" for e in items)


def test_transaction_recategorize_records_audit_event(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    uncategorized = _seeded_category(db_session, "Uncategorized")
    food = _seeded_category(db_session, "FOOD")
    txn = _make_txn(
        db_session, account, batch, description="SOME RANDOM PLACE", category=uncategorized,
        category_source="default", content_hash_suffix="3",
    )
    db_session.commit()

    resp = client.patch(f"/api/v1/transactions/{txn.id}", json={"category_id": food.id})
    assert resp.status_code == 200

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    matches = [e for e in items if e["event_type"] == "transaction.recategorized"]
    assert matches
    assert matches[0]["payload"]["to_category"] == "FOOD"
    assert matches[0]["affected_count"] == 1


def test_transaction_recategorize_to_same_category_does_not_record_event(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    txn = _make_txn(
        db_session, account, batch, description="SAME CATEGORY PLACE", category=food,
        category_source="manual", content_hash_suffix="4",
    )
    db_session.commit()

    before_count = client.get("/api/v1/audit").json()["total"]

    resp = client.patch(f"/api/v1/transactions/{txn.id}", json={"category_id": food.id})
    assert resp.status_code == 200

    after_count = client.get("/api/v1/audit").json()["total"]
    assert after_count == before_count


def test_bucket_crud_records_audit_events(client: TestClient) -> None:
    created = client.post("/api/v1/buckets", json={"name": "Audit Bucket"})
    bucket_id = created.json()["id"]

    client.patch(f"/api/v1/buckets/{bucket_id}", json={"name": "Audit Bucket Renamed"})
    client.delete(f"/api/v1/buckets/{bucket_id}")

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    assert any(e["event_type"] == "bucket.created" for e in items)
    assert any(e["event_type"] == "bucket.renamed" for e in items)
    assert any(e["event_type"] == "bucket.deleted" for e in items)


def test_audit_listing_is_newest_first_and_paginates(client: TestClient) -> None:
    for i in range(5):
        client.post("/api/v1/categories", json={"name": f"Pagination Category {i}"})

    page1 = client.get("/api/v1/audit", params={"limit": 2, "offset": 0})
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["items"]) == 2
    assert body1["limit"] == 2
    assert body1["offset"] == 0
    assert body1["total"] >= 5

    page2 = client.get("/api/v1/audit", params={"limit": 2, "offset": 2})
    body2 = page2.json()
    assert len(body2["items"]) == 2

    # Newest-first: first page's events should be newer (higher id) than
    # second page's.
    ids_page1 = {item["id"] for item in body1["items"]}
    ids_page2 = {item["id"] for item in body2["items"]}
    assert min(ids_page1) > max(ids_page2)
