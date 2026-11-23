"""API tests for category CRUD, keyword management, and impact-preview."""
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
    account = Account(workspace_id=_ws_id(db_session), institution_id=institution.id, account_hint="88888", display_name="Test Account", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        workspace_id=_ws_id(db_session),
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


# --- Clash reconciliation --------------------------------------------------
# A clash is a description claimed by 2+ categories. "COSTCO GAS" is the
# canonical real-world case: GAS (p0) silently beats COSTCO (p10).


def test_clashes_lists_rows_claimed_by_multiple_categories(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    _make_txn(
        db_session,
        account,
        batch,
        description="COSTCO GAS #0677 BURBANK CA",
        category=gas,
        category_source="keyword",
        content_hash_suffix="1",
    )
    db_session.commit()

    body = client.get("/api/v1/categories/clashes").json()

    assert body["total"] == 1
    item = body["items"][0]
    names = {c["category_name"] for c in item["claims"]}
    assert {"GAS", "COSTCO"} <= names

    winner = next(c for c in item["claims"] if c["is_winner"])
    assert winner["category_name"] == "GAS"
    assert item["transfer_decided"] is False


def test_clashes_excludes_manual_rows_by_default(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    costco = _seeded_category(db_session, "COSTCO")
    # The user already had the final say on this row.
    _make_txn(
        db_session,
        account,
        batch,
        description="COSTCO GAS #0677 BURBANK CA",
        category=costco,
        category_source="manual",
        content_hash_suffix="2",
    )
    db_session.commit()

    default_body = client.get("/api/v1/categories/clashes").json()
    assert default_body["total"] == 0
    assert default_body["settled_count"] == 1

    included = client.get(
        "/api/v1/categories/clashes", params={"include_settled": "true"}
    ).json()
    assert included["total"] == 1
    assert included["items"][0]["is_settled"] is True


def test_clash_flags_transfer_decided_rows(client: TestClient, db_session: Session) -> None:
    """A transfer-stage win happens before priority is consulted, so the
    UI must not offer a reorder as the fix."""
    account, batch = _make_batch(db_session)
    transfers = _seeded_category(db_session, "Payments & Transfers")
    _make_txn(
        db_session,
        account,
        batch,
        description="AMAZON MKTPLACE PMTS",
        category=transfers,
        category_source="transfer",
        content_hash_suffix="3",
    )
    db_session.commit()

    item = client.get("/api/v1/categories/clashes").json()["items"][0]

    assert item["transfer_decided"] is True
    winner = next(c for c in item["claims"] if c["is_winner"])
    assert winner["stage"] == "transfer"
    # AMAZON has the *better* priority yet still loses — the exact trap.
    amazon = next(c for c in item["claims"] if c["category_name"] == "AMAZON")
    assert amazon["priority"] < winner["priority"]


def test_resolve_clash_row_scope_pins_only_that_row_as_manual(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    a = _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="keyword", content_hash_suffix="4")
    b = _make_txn(db_session, account, batch, description="COSTCO GAS #2", category=gas, category_source="keyword", content_hash_suffix="5")
    db_session.commit()
    a_id, b_id = a.id, b.id

    resp = client.post(
        "/api/v1/categories/clashes/resolve",
        json={"transaction_ids": [a_id], "category_id": costco.id, "scope": "row"},
    )
    assert resp.status_code == 200
    assert resp.json()["resolved_count"] == 1

    db_session.expire_all()
    assert db_session.get(Transaction, a_id).category_source == "manual"
    assert db_session.get(Transaction, a_id).category_id == costco.id
    # The sibling is untouched under row scope.
    assert db_session.get(Transaction, b_id).category_source == "keyword"


def test_resolve_clash_all_matching_pins_every_sibling(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    a = _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="keyword", content_hash_suffix="6")
    b = _make_txn(db_session, account, batch, description="COSTCO GAS #2", category=gas, category_source="keyword", content_hash_suffix="7")
    db_session.commit()
    ids = [a.id, b.id]

    resp = client.post(
        "/api/v1/categories/clashes/resolve",
        json={
            "transaction_ids": [ids[0]],
            "category_id": costco.id,
            "scope": "all_matching",
            "keyword": "COSTCO GAS",
        },
    )
    assert resp.json()["resolved_count"] == 2

    db_session.expire_all()
    for tid in ids:
        assert db_session.get(Transaction, tid).category_id == costco.id
        assert db_session.get(Transaction, tid).category_source == "manual"


def test_resolve_clash_all_matching_requires_keyword(
    client: TestClient, db_session: Session
) -> None:
    costco = _seeded_category(db_session, "COSTCO")
    db_session.commit()
    resp = client.post(
        "/api/v1/categories/clashes/resolve",
        json={"transaction_ids": [1], "category_id": costco.id, "scope": "all_matching"},
    )
    assert resp.status_code == 422


def test_resolve_clash_unknown_category_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/categories/clashes/resolve",
        json={"transaction_ids": [1], "category_id": 999999},
    )
    assert resp.status_code == 404


def test_resolved_clash_survives_recategorize_all(
    client: TestClient, db_session: Session
) -> None:
    """The whole point of writing 'manual': the user's decision must not
    be undone by any later rules pass."""
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    txn = _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="keyword", content_hash_suffix="8")
    db_session.commit()
    txn_id = txn.id

    client.post(
        "/api/v1/categories/clashes/resolve",
        json={"transaction_ids": [txn_id], "category_id": costco.id, "scope": "row"},
    )
    client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False})

    db_session.expire_all()
    after = db_session.get(Transaction, txn_id)
    assert after.category_id == costco.id
    assert after.category_source == "manual"


def test_reprioritize_dry_run_reports_without_writing(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    original_priority = costco.priority
    _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="keyword", content_hash_suffix="9")
    db_session.commit()

    resp = client.post(
        "/api/v1/categories/reprioritize",
        json={"priorities": {str(costco.id): -1}, "dry_run": True},
    )
    body = resp.json()

    assert body["dry_run"] is True
    assert body["candidate_count"] == 1
    assert body["affected_count"] == 0
    assert body["moves"][0]["to_category_name"] == "COSTCO"

    db_session.expire_all()
    assert db_session.get(Category, costco.id).priority == original_priority


def test_reprioritize_applied_moves_rows_and_persists_priority(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    txn = _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="keyword", content_hash_suffix="b")
    db_session.commit()
    txn_id = txn.id

    body = client.post(
        "/api/v1/categories/reprioritize",
        json={"priorities": {str(costco.id): -1}, "dry_run": False},
    ).json()

    assert body["affected_count"] == 1

    db_session.expire_all()
    assert db_session.get(Category, costco.id).priority == -1
    assert db_session.get(Transaction, txn_id).category_id == costco.id


def test_reprioritize_never_moves_manual_rows(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    txn = _make_txn(db_session, account, batch, description="COSTCO GAS #1", category=gas, category_source="manual", content_hash_suffix="c")
    db_session.commit()
    txn_id = txn.id

    body = client.post(
        "/api/v1/categories/reprioritize",
        json={"priorities": {str(costco.id): -1}, "dry_run": False},
    ).json()

    assert body["affected_count"] == 0
    db_session.expire_all()
    assert db_session.get(Transaction, txn_id).category_id == gas.id
    assert db_session.get(Transaction, txn_id).category_source == "manual"


def test_reprioritize_unknown_category_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/categories/reprioritize", json={"priorities": {"999999": 1}}
    )
    assert resp.status_code == 404


def test_manual_resolve_clears_matched_keyword(
    client: TestClient, db_session: Session
) -> None:
    """A person's choice is not a rule match — the keyword that used to
    explain the row must not linger and misreport why it's there."""
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    txn = _make_txn(
        db_session, account, batch, description="COSTCO GAS #1",
        category=gas, category_source="keyword", content_hash_suffix="k",
    )
    txn.matched_keyword = "GAS"
    db_session.commit()
    txn_id = txn.id

    client.post(
        "/api/v1/categories/clashes/resolve",
        json={"transaction_ids": [txn_id], "category_id": costco.id, "scope": "row"},
    )

    db_session.expire_all()
    after = db_session.get(Transaction, txn_id)
    assert after.category_source == "manual"
    assert after.matched_keyword is None


def test_recategorize_all_records_the_new_matched_keyword(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    uncategorized = _seeded_category(db_session, "Uncategorized")
    txn = _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=uncategorized, category_source="default", content_hash_suffix="m",
    )
    db_session.commit()
    txn_id = txn.id

    client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False})

    db_session.expire_all()
    after = db_session.get(Transaction, txn_id)
    assert after.category_source == "keyword"
    assert after.matched_keyword == "CHIPOTLE"


# --- Delete category: preview + re-match -----------------------------------
# Deleting a category removes its keywords too, so its rows have to go
# somewhere. Previously they were all parked in Uncategorized even when
# another category's keywords would happily claim them.


def test_delete_preview_reports_where_rows_would_land(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    subs = _seeded_category(db_session, "STREAMING")
    # CHIPOTLE is a FOOD keyword, so this row has somewhere real to go.
    _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=subs, category_source="keyword", content_hash_suffix="p",
    )
    db_session.commit()

    body = client.get(f"/api/v1/categories/{subs.id}/delete-preview").json()

    assert body["affected_count"] == 1
    assert body["sample"][0]["new_category_name"] == "FOOD"


def test_delete_preview_writes_nothing(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    subs = _seeded_category(db_session, "STREAMING")
    txn = _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=subs, category_source="keyword", content_hash_suffix="q",
    )
    db_session.commit()
    txn_id, subs_id = txn.id, subs.id

    client.get(f"/api/v1/categories/{subs_id}/delete-preview")

    db_session.expire_all()
    assert db_session.get(Category, subs_id) is not None
    assert db_session.get(Transaction, txn_id).category_id == subs_id


def test_delete_with_rematch_places_rows_by_remaining_rules(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    subs = _seeded_category(db_session, "STREAMING")
    food = _seeded_category(db_session, "FOOD")
    matched = _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=subs, category_source="keyword", content_hash_suffix="r",
    )
    # Nothing claims this one, so it should still fall to Uncategorized.
    orphan = _make_txn(
        db_session, account, batch, description="ZZZ NOTHING MATCHES THIS",
        category=subs, category_source="keyword", content_hash_suffix="s",
    )
    db_session.commit()
    # Note the tuple order: orphan.id, not food.id, is the third element —
    # read the ids explicitly so a mismatched unpack can't silently pass.
    matched_id = matched.id
    orphan_id = orphan.id
    food_id = food.id

    resp = client.delete(f"/api/v1/categories/{subs.id}?rematch=true")
    assert resp.status_code == 200
    assert resp.json()["rematched_transaction_count"] == 1

    db_session.expire_all()
    assert db_session.get(Transaction, matched_id).category_id == food_id
    assert db_session.get(Transaction, matched_id).matched_keyword == "CHIPOTLE"
    uncategorized = _seeded_category(db_session, "Uncategorized")
    assert db_session.get(Transaction, orphan_id).category_id == uncategorized.id


def test_delete_without_rematch_keeps_the_old_uncategorized_behavior(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    subs = _seeded_category(db_session, "STREAMING")
    txn = _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=subs, category_source="keyword", content_hash_suffix="t",
    )
    db_session.commit()
    txn_id = txn.id

    resp = client.delete(f"/api/v1/categories/{subs.id}")
    assert resp.json()["rematched_transaction_count"] == 0

    db_session.expire_all()
    uncategorized = _seeded_category(db_session, "Uncategorized")
    assert db_session.get(Transaction, txn_id).category_id == uncategorized.id


def test_delete_rematch_never_moves_manual_rows_to_a_rules_category(
    client: TestClient, db_session: Session
) -> None:
    """A manual row still has to come off the deleted category, but the
    rules don't get to pick its new home — it lands in Uncategorized for
    the user to re-decide."""
    account, batch = _make_batch(db_session)
    subs = _seeded_category(db_session, "STREAMING")
    txn = _make_txn(
        db_session, account, batch, description="CHIPOTLE 1521",
        category=subs, category_source="manual", content_hash_suffix="u",
    )
    db_session.commit()
    txn_id = txn.id

    client.delete(f"/api/v1/categories/{subs.id}?rematch=true")

    db_session.expire_all()
    uncategorized = _seeded_category(db_session, "Uncategorized")
    after = db_session.get(Transaction, txn_id)
    assert after.category_id == uncategorized.id
    assert after.category_id != _seeded_category(db_session, "FOOD").id


def test_delete_preview_rejects_system_categories(client: TestClient, db_session: Session) -> None:
    """Previewing removal of Payments & Transfers / Uncategorized would
    build a rule set the categorizer can't construct (it requires both),
    and they can't be deleted anyway — so 409, not a 500."""
    for name in ("Payments & Transfers", "Uncategorized"):
        category = _seeded_category(db_session, name)
        resp = client.get(f"/api/v1/categories/{category.id}/delete-preview")
        assert resp.status_code == 409, name
        assert resp.json()["detail"]["code"] == "SYSTEM_CATEGORY_UNDELETABLE"


# --- Clash dismissals ------------------------------------------------------
# A conflict where priority already chose correctly is noise, not work.
# Dismissing records a judgment about the RULES and leaves the row's
# categorization alone — unlike resolving, which pins it as 'manual'.


def _clash_rows(client: TestClient) -> dict:
    return client.get("/api/v1/categories/clashes", params={"limit": 500}).json()


def test_rule_dismissal_hides_all_rows_of_that_pairing(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    for i, suffix in enumerate("vw"):
        _make_txn(
            db_session, account, batch, description=f"COSTCO GAS #{i}",
            category=gas, category_source="keyword", content_hash_suffix=suffix,
        )
    db_session.commit()

    assert _clash_rows(client)["total"] == 2

    resp = client.post(
        "/api/v1/categories/clashes/dismiss",
        json={"winner_category_id": gas.id, "loser_category_id": costco.id},
    )
    assert resp.status_code == 201

    after = _clash_rows(client)
    assert after["total"] == 0
    # The queue must not look empty when it is merely suppressed.
    assert after["dismissed_count"] == 2


def test_dismissal_does_not_change_the_transaction(
    client: TestClient, db_session: Session
) -> None:
    """The whole point: a dismissal judges the rules, not the row — so a
    later rule fix still reaches it. Resolving would pin it 'manual'."""
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    txn = _make_txn(
        db_session, account, batch, description="COSTCO GAS #1",
        category=gas, category_source="keyword", content_hash_suffix="x",
    )
    txn.matched_keyword = "GAS"
    db_session.commit()
    txn_id, gas_id = txn.id, gas.id

    client.post(
        "/api/v1/categories/clashes/dismiss",
        json={"winner_category_id": gas.id, "loser_category_id": costco.id},
    )

    db_session.expire_all()
    after = db_session.get(Transaction, txn_id)
    assert after.category_id == gas_id
    assert after.category_source == "keyword"
    # Still 'keyword'-sourced, so a later rule fix reaches it. Resolving
    # instead would have overwritten this with manual/None.
    assert after.matched_keyword == "GAS"


def test_row_dismissal_scopes_to_one_record(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    first = _make_txn(
        db_session, account, batch, description="COSTCO GAS #1",
        category=gas, category_source="keyword", content_hash_suffix="y",
    )
    _make_txn(
        db_session, account, batch, description="COSTCO GAS #2",
        category=gas, category_source="keyword", content_hash_suffix="z",
    )
    db_session.commit()

    client.post(
        "/api/v1/categories/clashes/dismiss",
        json={
            "winner_category_id": gas.id,
            "loser_category_id": costco.id,
            "transaction_id": first.id,
        },
    )

    after = _clash_rows(client)
    assert after["total"] == 1
    assert after["dismissed_count"] == 1
    assert after["items"][0]["transaction_id"] != first.id


def test_dismiss_is_idempotent(client: TestClient, db_session: Session) -> None:
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    db_session.commit()
    body = {"winner_category_id": gas.id, "loser_category_id": costco.id}

    first = client.post("/api/v1/categories/clashes/dismiss", json=body).json()
    second = client.post("/api/v1/categories/clashes/dismiss", json=body).json()

    assert first["id"] == second["id"]
    assert client.get("/api/v1/categories/clashes/dismissals").json()["total"] == 1


def test_undismiss_restores_the_conflicts(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    _make_txn(
        db_session, account, batch, description="COSTCO GAS #1",
        category=gas, category_source="keyword", content_hash_suffix="A",
    )
    db_session.commit()

    created = client.post(
        "/api/v1/categories/clashes/dismiss",
        json={"winner_category_id": gas.id, "loser_category_id": costco.id},
    ).json()
    assert _clash_rows(client)["total"] == 0

    resp = client.delete(f"/api/v1/categories/clashes/dismissals/{created['id']}")
    assert resp.status_code == 204
    assert _clash_rows(client)["total"] == 1


def test_dismissal_list_reports_hidden_counts(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    gas = _seeded_category(db_session, "GAS")
    costco = _seeded_category(db_session, "COSTCO")
    for i, suffix in enumerate("BC"):
        _make_txn(
            db_session, account, batch, description=f"COSTCO GAS #{i}",
            category=gas, category_source="keyword", content_hash_suffix=suffix,
        )
    db_session.commit()

    client.post(
        "/api/v1/categories/clashes/dismiss",
        json={"winner_category_id": gas.id, "loser_category_id": costco.id},
    )

    body = client.get("/api/v1/categories/clashes/dismissals").json()
    assert body["total"] == 1
    assert body["hidden_total"] == 2
    assert body["items"][0]["hidden_count"] == 2
    assert body["items"][0]["winner_category_name"] == "GAS"
    assert body["items"][0]["loser_category_name"] == "COSTCO"


def test_dismiss_unknown_category_404(client: TestClient, db_session: Session) -> None:
    gas = _seeded_category(db_session, "GAS")
    db_session.commit()
    resp = client.post(
        "/api/v1/categories/clashes/dismiss",
        json={"winner_category_id": gas.id, "loser_category_id": 999999},
    )
    assert resp.status_code == 404


def test_undismiss_unknown_404(client: TestClient) -> None:
    assert client.delete("/api/v1/categories/clashes/dismissals/999999").status_code == 404
