"""API tests for GET /transactions (filters/sort/pagination/exclusion)
and PATCH /transactions/{id} (manual recategorize + stickiness)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Account, Category, Institution, Transaction


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
    from app.models import IngestBatch

    institution = db_session.query(Institution).filter(Institution.code == institution_code).one()
    account = Account(workspace_id=_ws_id(db_session), institution_id=institution.id, account_hint="99999", display_name="Test Amex", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        workspace_id=_ws_id(db_session),
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
        workspace_id=_ws_id(db_session),
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


def test_list_transactions_income_always_included(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    income = _seeded_category(db_session, "Income")
    transfers = _seeded_category(db_session, "Payments & Transfers")
    food = _seeded_category(db_session, "FOOD")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="3000.00",
        description="PAYROLL", category=income, category_source="keyword",
        content_hash_suffix="1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 2), amount="-50.00",
        description="AUTOPAY PAYMENT THANK YOU", category=transfers, category_source="transfer",
        content_hash_suffix="2",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 3), amount="-10.00",
        description="CHIPOTLE MEXICAN GRILL", category=food, category_source="keyword",
        content_hash_suffix="3",
    )
    db_session.commit()

    # Income shows up even by default, unlike transfers — only transfers
    # are gated behind include_excluded.
    default_resp = client.get("/api/v1/transactions")
    assert default_resp.status_code == 200
    default_body = default_resp.json()
    assert default_body["total"] == 2
    assert any(item["category_name"] == "Income" for item in default_body["items"])
    assert all(item["category_name"] != "Payments & Transfers" for item in default_body["items"])

    included_resp = client.get("/api/v1/transactions", params={"include_excluded": "true"})
    included_body = included_resp.json()
    assert included_body["total"] == 3


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


def test_list_exclude_category_ids_keeps_uncategorized(
    client: TestClient, db_session: Session
) -> None:
    """The Budget page lists "everything not linked to a budget expense"
    by excluding the budgeted category ids — uncategorized rows must
    survive that exclusion (NULL NOT IN (...) is NULL, not true)."""
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 10), amount="-30.00",
        description="TACOS", category=food, category_source="keyword", content_hash_suffix="x1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 11), amount="-40.00",
        description="SHELL", category=gas, category_source="keyword", content_hash_suffix="x2",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 12), amount="-25.00",
        description="MYSTERY CHARGE", category=None, category_source="default",
        content_hash_suffix="x3",
    )
    db_session.commit()

    resp = client.get(
        "/api/v1/transactions",
        params={"exclude_category_ids": [food.id], "include_excluded": "true"},
    )
    assert resp.status_code == 200
    descriptions = {item["description"] for item in resp.json()["items"]}
    assert descriptions == {"SHELL", "MYSTERY CHARGE"}

    # Excluding every real category leaves only the uncategorized row.
    both = client.get(
        "/api/v1/transactions",
        params={
            "exclude_category_ids": [food.id, gas.id],
            "include_excluded": "true",
        },
    ).json()
    assert [item["description"] for item in both["items"]] == ["MYSTERY CHARGE"]
    assert both["total"] == 1

    # The exclusion also bounds the facet options, since it's a fixed
    # scope rather than a dimension the user toggles.
    facets = client.get(
        "/api/v1/transactions/facets",
        params={"exclude_category_ids": [food.id], "include_excluded": "true"},
    ).json()
    assert food.id not in facets["category_ids"]
    assert gas.id in facets["category_ids"]


def test_list_outflows_only_drops_income(client: TestClient, db_session: Session) -> None:
    """`outflows_only` keeps money-out rows only. It must drop "Income"
    too — `include_excluded` has a hard-coded carve-out that always
    lets Income through, so the Budget page's unbudgeted spend analysis
    can't rely on the category filter alone to keep a payroll deposit
    out of its "unaccounted-for spend" list."""
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    income = _seeded_category(db_session, "Income")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 10), amount="-30.00",
        description="TACOS", category=food, category_source="keyword", content_hash_suffix="o1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 15), amount="4130.32",
        description="SERVE OPERATING PAYROLL", category=income, category_source="keyword",
        content_hash_suffix="o2",
    )
    db_session.commit()

    # Without the flag, the payroll deposit is present (Income is always
    # included) — that's the behaviour being guarded against.
    baseline = client.get("/api/v1/transactions").json()
    assert "SERVE OPERATING PAYROLL" in {i["description"] for i in baseline["items"]}

    resp = client.get("/api/v1/transactions", params={"outflows_only": "true"})
    assert resp.status_code == 200
    descriptions = {item["description"] for item in resp.json()["items"]}
    assert descriptions == {"TACOS"}
    assert all(Decimal(item["amount"]) < 0 for item in resp.json()["items"])


def test_facets_narrow_by_other_filters_but_not_own_dimension(
    client: TestClient, db_session: Session
) -> None:
    account_a, batch_a = _make_batch(db_session, institution_code="amex")
    account_b, batch_b = _make_batch(db_session, institution_code="schwab")
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    # account_a: Food in Oct, Gas in Sep. account_b: Food in Nov only.
    _make_txn(
        db_session, account_a, batch_a, txn_date=date(2026, 10, 5), amount="-10.00",
        description="A FOOD OCT", category=food, category_source="keyword", content_hash_suffix="f1",
    )
    _make_txn(
        db_session, account_a, batch_a, txn_date=date(2026, 9, 5), amount="-20.00",
        description="A GAS SEP", category=gas, category_source="keyword", content_hash_suffix="f2",
    )
    _make_txn(
        db_session, account_b, batch_b, txn_date=date(2026, 11, 5), amount="-15.00",
        description="B FOOD NOV", category=food, category_source="keyword", content_hash_suffix="f3",
    )
    db_session.commit()

    # Filtering to account_b should narrow categories to just Food and
    # months to just Nov, but account_ids itself should still list BOTH
    # accounts (an account's own chip ignores the account filter).
    resp = client.get(
        "/api/v1/transactions/facets",
        params={"account_ids": [account_b.id], "include_excluded": "true"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["account_ids"]) == {account_a.id, account_b.id}
    assert body["category_ids"] == [food.id]
    assert body["month_keys"] == ["2026-11"]

    # Filtering to Gas should narrow accounts to just account_a and
    # months to just Sep, but category_ids itself still lists both.
    resp2 = client.get(
        "/api/v1/transactions/facets",
        params={"category_ids": [gas.id], "include_excluded": "true"},
    )
    body2 = resp2.json()
    assert body2["account_ids"] == [account_a.id]
    assert set(body2["category_ids"]) == {food.id, gas.id}
    assert body2["month_keys"] == ["2026-09"]

    # Filtering to Oct..Oct should narrow accounts/categories to
    # account_a/Food, but month_keys itself ignores the date filter.
    resp3 = client.get(
        "/api/v1/transactions/facets",
        params={"date_from": "2026-10-01", "date_to": "2026-10-31", "include_excluded": "true"},
    )
    body3 = resp3.json()
    assert body3["account_ids"] == [account_a.id]
    assert body3["category_ids"] == [food.id]
    assert set(body3["month_keys"]) == {"2026-09", "2026-10", "2026-11"}


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


def test_bulk_recategorize_updates_all_rows_as_one_audit_event(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    txns = [
        _make_txn(
            db_session, account, batch, txn_date=date(2026, 10, 1 + i), amount="-5.00",
            description=f"BULK MERCHANT {i}", category=food, category_source="keyword",
            content_hash_suffix=f"bulk{i}",
        )
        for i in range(3)
    ]
    db_session.commit()
    ids = [t.id for t in txns]

    before_audit_total = client.get("/api/v1/audit").json()["total"]

    resp = client.post(
        "/api/v1/transactions/bulk-recategorize",
        json={"transaction_ids": ids, "category_id": gas.id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["affected_count"] == 3
    assert body["category_id"] == gas.id
    assert body["category_name"] == "GAS"

    for t in txns:
        db_session.refresh(t)
        assert t.category_id == gas.id
        assert t.category_source == "bulk"

    audit = client.get("/api/v1/audit")
    items = audit.json()["items"]
    assert audit.json()["total"] == before_audit_total + 1
    matches = [e for e in items if e["event_type"] == "transaction.bulk_recategorized"]
    assert len(matches) == 1
    assert matches[0]["affected_count"] == 3


def test_bulk_recategorize_unknown_category_404(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    txn = _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-5.00",
        description="SOME PLACE", category=food, category_source="keyword",
        content_hash_suffix="bulk404",
    )
    db_session.commit()

    resp = client.post(
        "/api/v1/transactions/bulk-recategorize",
        json={"transaction_ids": [txn.id], "category_id": 999999},
    )
    assert resp.status_code == 404


def test_bulk_recategorized_rows_sticky_against_apply_to_existing(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    uncategorized = _seeded_category(db_session, "Uncategorized")
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    txn = _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 1), amount="-10.00",
        description="PEETS COFFEE SHOP BULK", category=uncategorized, category_source="default",
        content_hash_suffix="bulksticky",
    )
    db_session.commit()

    bulk_resp = client.post(
        "/api/v1/transactions/bulk-recategorize",
        json={"transaction_ids": [txn.id], "category_id": gas.id},
    )
    assert bulk_resp.status_code == 200

    add_resp = client.post(
        f"/api/v1/categories/{food.id}/keywords",
        json={"keyword": "PEETS COFFEE SHOP BULK", "apply_to_existing": True},
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["applied_count"] == 0

    db_session.refresh(txn)
    assert txn.category_id == gas.id
    assert txn.category_source == "bulk"


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


# --- POST /transactions/recategorize-all -----------------------------------
# Categorization runs only at ingest, so rows inserted before a keyword
# existed keep their original category. These cover the catch-up pass.


def _uncategorized(db_session: Session) -> Category:
    return db_session.query(Category).filter(Category.name == "Uncategorized").one()


def _transfers(db_session: Session) -> Category:
    return db_session.query(Category).filter(Category.name == "Payments & Transfers").one()


def test_recategorize_all_dry_run_reports_without_writing(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    # A PMT row stranded in Uncategorized, exactly like a row ingested
    # before the transfer keywords were seeded.
    txn = _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT CA0D12427086473",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()
    stranded_id = txn.id

    response = client.post("/api/v1/transactions/recategorize-all", json={"dry_run": True})
    assert response.status_code == 200
    body = response.json()

    assert body["dry_run"] is True
    assert body["candidate_count"] == 1
    assert body["affected_count"] == 0

    move = next(m for m in body["moves"] if m["transaction_id"] == stranded_id)
    assert move["from_category_name"] == "Uncategorized"
    assert move["to_category_name"] == "Payments & Transfers"
    assert move["to_source"] == "transfer"

    # Nothing was written.
    db_session.expire_all()
    after = db_session.get(Transaction, stranded_id)
    assert after.category_id == _uncategorized(db_session).id
    assert after.category_source == "default"


def test_recategorize_all_applies_and_fixes_stranded_pmt_row(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    txn = _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT CA0D12427086473",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()
    stranded_id = txn.id

    response = client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False})
    assert response.status_code == 200
    body = response.json()

    assert body["dry_run"] is False
    assert body["affected_count"] == 1

    db_session.expire_all()
    after = db_session.get(Transaction, stranded_id)
    assert after.category_id == _transfers(db_session).id
    assert after.category_source == "transfer"


def test_recategorize_all_defaults_to_dry_run_with_no_body(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    txn = _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()
    stranded_id = txn.id

    response = client.post("/api/v1/transactions/recategorize-all")
    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["affected_count"] == 0

    db_session.expire_all()
    assert db_session.get(Transaction, stranded_id).category_source == "default"


def test_recategorize_all_never_touches_manual_or_bulk_rows(
    client: TestClient, db_session: Session
) -> None:
    account, batch = _make_batch(db_session)
    uncategorized = _uncategorized(db_session)
    # Both rows would match a transfer keyword, but a person deliberately
    # put them where they are.
    manual = _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-10.00",
        description="SOME PMT I FILED BY HAND",
        category=uncategorized,
        category_source="manual",
        content_hash_suffix="b",
    )
    bulk = _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 10),
        amount="-11.00",
        description="ANOTHER PMT I BULK SORTED",
        category=uncategorized,
        category_source="bulk",
        content_hash_suffix="c",
    )
    db_session.commit()
    manual_id, bulk_id = manual.id, bulk.id

    body = client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False}).json()

    assert body["affected_count"] == 0
    assert body["skipped_sticky_count"] == 2

    db_session.expire_all()
    assert db_session.get(Transaction, manual_id).category_source == "manual"
    assert db_session.get(Transaction, bulk_id).category_source == "bulk"


def test_recategorize_all_is_idempotent(client: TestClient, db_session: Session) -> None:
    account, batch = _make_batch(db_session)
    _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()

    first = client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False}).json()
    assert first["affected_count"] == 1

    # Rules already satisfied, so a second pass finds nothing to do.
    second = client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False}).json()
    assert second["candidate_count"] == 0
    assert second["affected_count"] == 0


def test_recategorize_all_records_one_audit_event_when_applied(
    client: TestClient, db_session: Session
) -> None:
    from app.models import AuditEvent

    account, batch = _make_batch(db_session)
    _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()

    client.post("/api/v1/transactions/recategorize-all", json={"dry_run": False})

    events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.event_type == "transaction.recategorized_all")
        .all()
    )
    assert len(events) == 1
    assert events[0].affected_count == 1


def test_recategorize_all_dry_run_records_no_audit_event(
    client: TestClient, db_session: Session
) -> None:
    from app.models import AuditEvent

    account, batch = _make_batch(db_session)
    _make_txn(
        db_session,
        account,
        batch,
        txn_date=date(2026, 9, 9),
        amount="-4000.00",
        description="CAPITAL ONE MOBILE PMT",
        category=_uncategorized(db_session),
        category_source="default",
    )
    db_session.commit()

    client.post("/api/v1/transactions/recategorize-all", json={"dry_run": True})

    assert (
        db_session.query(AuditEvent)
        .filter(AuditEvent.event_type == "transaction.recategorized_all")
        .count()
        == 0
    )
