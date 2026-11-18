"""API tests for category CRUD, keyword management, and impact-preview."""
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
    category_source: str = "default",
    content_hash_suffix: str = "a",
    amount: str = "-10.00",
) -> Transaction:
    txn = Transaction(
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


def test_list_categories_includes_keywords_and_counts(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    _make_txn(db_session, account, batch, description="CHIPOTLE", category=food, category_source="keyword", content_hash_suffix="1")
    db_session.commit()

    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    categories = {c["name"]: c for c in resp.json()}
    assert "FOOD" in categories
    assert categories["FOOD"]["transaction_count"] >= 1
    assert any(k["keyword"] == "CHIPOTLE" for k in categories["FOOD"]["keywords"])
    assert categories["Uncategorized"]["is_system"] is True
    # bucket_id + group (bucket name, raw uppercase) are both present.
    assert categories["FOOD"]["bucket_id"] is not None
    assert categories["FOOD"]["group"] == "LIFESTYLE"
    assert categories["Uncategorized"]["group"] == "OTHER"


def test_create_category(client: TestClient) -> None:
    resp = client.post("/api/v1/categories", json={"name": "Test Subscriptions A"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Subscriptions A"
    assert body["is_system"] is False
    assert body["excluded_from_analytics"] is False
    # No bucket_id given -> defaults to OTHER.
    assert body["group"] == "OTHER"
    assert body["bucket_id"] is not None


def test_create_category_with_explicit_bucket_id(client: TestClient, db_session: Session) -> None:
    bucket_resp = client.post("/api/v1/buckets", json={"name": "Explicit Bucket"})
    bucket_id = bucket_resp.json()["id"]

    resp = client.post(
        "/api/v1/categories",
        json={"name": "Test Subscriptions Explicit", "bucket_id": bucket_id},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["bucket_id"] == bucket_id
    assert body["group"] == "EXPLICIT BUCKET"


def test_create_category_duplicate_name_409(client: TestClient) -> None:
    client.post("/api/v1/categories", json={"name": "Test Subscriptions B"})
    resp = client.post("/api/v1/categories", json={"name": "Test Subscriptions B"})
    assert resp.status_code == 409


def test_rename_category_returns_affected_count(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    _make_txn(db_session, account, batch, description="CHIPOTLE", category=food, category_source="keyword", content_hash_suffix="2")
    _make_txn(db_session, account, batch, description="TACOS", category=food, category_source="keyword", content_hash_suffix="3")
    db_session.commit()

    resp = client.patch(f"/api/v1/categories/{food.id}", json={"name": "Dining & Coffee"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"]["name"] == "Dining & Coffee"
    assert body["affected_transaction_count"] == 2


def test_patch_category_bucket_id_changes_group(client: TestClient, db_session: Session) -> None:
    from app.models import Category

    bucket_resp = client.post("/api/v1/buckets", json={"name": "Patch Target Bucket"})
    bucket_id = bucket_resp.json()["id"]

    food = _seeded_category(db_session, "FOOD")
    original_bucket_id = food.bucket_id

    resp = client.patch(f"/api/v1/categories/{food.id}", json={"bucket_id": bucket_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"]["bucket_id"] == bucket_id
    assert body["category"]["group"] == "PATCH TARGET BUCKET"

    db_session.expire_all()
    refreshed = db_session.get(Category, food.id)
    assert refreshed.bucket_id == bucket_id
    assert refreshed.bucket_id != original_bucket_id


def test_delete_category_reassigns_to_uncategorized(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    _make_txn(db_session, account, batch, description="CHEVRON", category=gas, category_source="keyword", content_hash_suffix="4")
    _make_txn(db_session, account, batch, description="SHELL", category=gas, category_source="keyword", content_hash_suffix="5")
    db_session.commit()

    resp = client.delete(f"/api/v1/categories/{gas.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted_category_id"] == gas.id
    assert body["reassigned_transaction_count"] == 2

    uncategorized = _seeded_category(db_session, "Uncategorized")
    reassigned = db_session.query(Transaction).filter(Transaction.description.in_(["CHEVRON", "SHELL"])).all()
    for txn in reassigned:
        db_session.refresh(txn)
        assert txn.category_id == uncategorized.id

    deleted_check = db_session.query(Category).filter(Category.id == gas.id).one_or_none()
    assert deleted_check is None


def test_delete_system_category_rejected_409(client: TestClient, db_session: Session) -> None:
    uncategorized = _seeded_category(db_session, "Uncategorized")
    resp = client.delete(f"/api/v1/categories/{uncategorized.id}")
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "SYSTEM_CATEGORY_UNDELETABLE"


def test_impact_preview_add_keyword_steals_from_uncategorized(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    uncategorized = _seeded_category(db_session, "Uncategorized")

    txn1 = _make_txn(
        db_session, account, batch, description="PEETS COFFEE #412", category=uncategorized,
        category_source="default", content_hash_suffix="6",
    )
    txn2 = _make_txn(
        db_session, account, batch, description="NOT MATCHING AT ALL", category=uncategorized,
        category_source="default", content_hash_suffix="7",
    )
    db_session.commit()

    resp = client.post(
        "/api/v1/categories/impact-preview",
        json={"action": "add_keyword", "category_id": food.id, "keyword": "peets coffee"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["affected_count"] == 1
    assert body["sample"][0]["id"] == txn1.id
    assert body["sample"][0]["new_category_name"] == "FOOD"
    assert not any(s["id"] == txn2.id for s in body["sample"])

    breakdown = body["breakdown"]
    assert len(breakdown) == 1
    assert breakdown[0]["from_category"] == "Uncategorized"
    assert breakdown[0]["to_category"] == "FOOD"
    assert breakdown[0]["count"] == 1


def test_impact_preview_respects_higher_priority_category(
    client: TestClient, db_session: Session
) -> None:
    """A proposed keyword must not steal a transaction if a
    higher-priority category's keyword already matches it under full
    categorizer precedence."""
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")  # priority 0, has keyword "GAS"
    food = _seeded_category(db_session, "FOOD")

    # "GAS" already matches via the Gas category (higher priority / lower
    # number than Food). Adding "STATION" to Food should NOT steal this
    # transaction since Gas's "GAS" keyword wins first.
    txn = _make_txn(
        db_session, account, batch, description="CHEVRON GAS STATION", category=gas,
        category_source="keyword", content_hash_suffix="8",
    )
    db_session.commit()

    resp = client.post(
        "/api/v1/categories/impact-preview",
        json={"action": "add_keyword", "category_id": food.id, "keyword": "station"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert not any(s["id"] == txn.id for s in body["sample"])
    assert body["affected_count"] == 0


def test_impact_preview_excludes_manual_transactions(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    uncategorized = _seeded_category(db_session, "Uncategorized")

    txn = _make_txn(
        db_session, account, batch, description="PEETS COFFEE SHOP", category=uncategorized,
        category_source="manual", content_hash_suffix="9",
    )
    db_session.commit()

    resp = client.post(
        "/api/v1/categories/impact-preview",
        json={"action": "add_keyword", "category_id": food.id, "keyword": "peets coffee"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert not any(s["id"] == txn.id for s in body["sample"])


def test_add_keyword_global_unique_conflict_409(client: TestClient, db_session: Session) -> None:
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    first = client.post(f"/api/v1/categories/{food.id}/keywords", json={"keyword": "UNIQUETOKEN123"})
    assert first.status_code == 201

    conflict = client.post(f"/api/v1/categories/{gas.id}/keywords", json={"keyword": "UNIQUETOKEN123"})
    assert conflict.status_code == 409
    detail = conflict.json()["detail"]
    assert detail["code"] == "KEYWORD_ALREADY_CLAIMED"
    assert detail["owning_category_id"] == food.id


def test_add_keyword_apply_to_existing_updates_rows(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    uncategorized = _seeded_category(db_session, "Uncategorized")

    txn = _make_txn(
        db_session, account, batch, description="PEETS COFFEE #412", category=uncategorized,
        category_source="default", content_hash_suffix="a",
    )
    db_session.commit()

    resp = client.post(
        f"/api/v1/categories/{food.id}/keywords",
        json={"keyword": "peets coffee", "apply_to_existing": True},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["keyword"]["keyword"] == "PEETS COFFEE"
    assert body["applied_count"] == 1

    db_session.refresh(txn)
    assert txn.category_id == food.id
    assert txn.category_source == "keyword"


def test_remove_keyword_with_reapply(client: TestClient, db_session: Session) -> None:
    # Use a keyword/description with no overlap with any other seeded
    # keyword, so removing it unambiguously falls through to Uncategorized.
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    uncategorized = _seeded_category(db_session, "Uncategorized")

    add_resp = client.post(
        f"/api/v1/categories/{food.id}/keywords",
        json={"keyword": "zzzquirky mart", "apply_to_existing": False},
    )
    assert add_resp.status_code == 201
    keyword_id = add_resp.json()["keyword"]["id"]

    txn = _make_txn(
        db_session, account, batch, description="ZZZQUIRKY MART #412", category=food,
        category_source="keyword", content_hash_suffix="b",
    )
    db_session.commit()

    del_resp = client.delete(f"/api/v1/categories/{food.id}/keywords/{keyword_id}", params={"reapply": "true"})
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["deleted_keyword_id"] == keyword_id
    assert body["reapplied_count"] == 1

    db_session.refresh(txn)
    assert txn.category_id == uncategorized.id
    assert txn.category_source == "default"


def test_remove_keyword_without_reapply_leaves_rows_unchanged(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")

    add_resp = client.post(f"/api/v1/categories/{food.id}/keywords", json={"keyword": "peets coffee"})
    keyword_id = add_resp.json()["keyword"]["id"]

    txn = _make_txn(
        db_session, account, batch, description="PEETS COFFEE #412", category=food,
        category_source="keyword", content_hash_suffix="c",
    )
    db_session.commit()

    del_resp = client.delete(f"/api/v1/categories/{food.id}/keywords/{keyword_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["reapplied_count"] == 0

    db_session.refresh(txn)
    assert txn.category_id == food.id
    assert txn.category_source == "keyword"
