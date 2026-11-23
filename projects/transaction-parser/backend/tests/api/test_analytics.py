"""API tests for /analytics/summary, /distribution, /timeseries."""
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
    account = Account(workspace_id=_ws_id(db_session), institution_id=institution.id, account_hint="77777", display_name="Test Account", kind="card")
    db_session.add(account)
    db_session.flush()
    batch = IngestBatch(
        workspace_id=_ws_id(db_session),
        filename="test.csv",
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
    txn_date: date,
    amount: str,
    description: str,
    category: Category | None,
    category_source: str = "default",
    content_hash_suffix: str = "a",
) -> Transaction:
    txn = Transaction(
        workspace_id=_ws_id(db_session),
        account_id=account.id,
        batch_id=batch.id,
        txn_date=txn_date,
        posted_date=txn_date,
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


def _seed_standard_set(db_session: Session):
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    transfers = _seeded_category(db_session, "Payments & Transfers")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 9, 10), amount="-20.00",
        description="CHIPOTLE", category=food, category_source="keyword", content_hash_suffix="1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 10), amount="-30.00",
        description="TACOS", category=food, category_source="keyword", content_hash_suffix="2",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 15), amount="1000.00",
        description="PAYROLL DEPOSIT", category=None, category_source="default", content_hash_suffix="3",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 20), amount="-500.00",
        description="AUTOPAY PAYMENT THANK YOU", category=transfers, category_source="transfer",
        content_hash_suffix="4",
    )
    db_session.commit()
    return account, batch, food, transfers


def test_summary_excludes_transfers_by_default(client: TestClient, db_session: Session) -> None:
    _seed_standard_set(db_session)

    resp = client.get("/api/v1/analytics/summary")
    assert resp.status_code == 200
    body = resp.json()
    # Food (50) only; transfer excluded.
    assert Decimal(body["total_spent"]) == Decimal("50.00")
    assert Decimal(body["total_in"]) == Decimal("1000.00")
    assert Decimal(body["net"]) == Decimal("950.00")
    assert body["transaction_count"] == 3  # 2 food + 1 payroll, transfer excluded

    included_resp = client.get("/api/v1/analytics/summary", params={"include_excluded": "true"})
    included_body = included_resp.json()
    assert Decimal(included_body["total_spent"]) == Decimal("550.00")
    assert included_body["transaction_count"] == 4


def test_distribution_no_transfers_by_default(client: TestClient, db_session: Session) -> None:
    _seed_standard_set(db_session)

    resp = client.get("/api/v1/analytics/distribution")
    assert resp.status_code == 200
    body = resp.json()
    names = {e["name"] for e in body["entries"]}
    assert "Payments & Transfers" not in names
    assert "FOOD" in names
    food_entry = next(e for e in body["entries"] if e["name"] == "FOOD")
    assert Decimal(food_entry["amount"]) == Decimal("50.00")

    included_resp = client.get("/api/v1/analytics/distribution", params={"include_excluded": "true"})
    included_names = {e["name"] for e in included_resp.json()["entries"]}
    assert "Payments & Transfers" in included_names


def test_distribution_exclude_category_ids_keeps_uncategorized(
    client: TestClient, db_session: Session
) -> None:
    """`exclude_category_ids` drops the named categories but must NOT
    drop uncategorized spend — the Budget page's unbudgeted breakdown
    excludes the budgeted categories and relies on "Uncategorized"
    still showing up (a plain SQL NOT IN would swallow it, since
    NULL NOT IN (...) is NULL, not true)."""
    account, batch = _make_batch(db_session)
    food = _seeded_category(db_session, "FOOD")
    gas = _seeded_category(db_session, "GAS")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 10), amount="-30.00",
        description="TACOS", category=food, category_source="keyword", content_hash_suffix="1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 11), amount="-40.00",
        description="SHELL", category=gas, category_source="keyword", content_hash_suffix="2",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 12), amount="-25.00",
        description="MYSTERY CHARGE", category=None, category_source="default",
        content_hash_suffix="3",
    )
    db_session.commit()

    resp = client.get(
        "/api/v1/analytics/distribution", params={"exclude_category_ids": [food.id]}
    )
    assert resp.status_code == 200
    body = resp.json()
    names = {e["name"] for e in body["entries"]}
    assert "FOOD" not in names
    assert names == {"GAS", "Uncategorized"}
    assert Decimal(body["total"]) == Decimal("65.00")

    # Excluding every real category leaves only the uncategorized spend.
    only_uncat = client.get(
        "/api/v1/analytics/distribution",
        params={"exclude_category_ids": [food.id, gas.id]},
    ).json()
    assert [e["name"] for e in only_uncat["entries"]] == ["Uncategorized"]
    assert Decimal(only_uncat["total"]) == Decimal("25.00")

    # Excluding nothing explicitly is the same as not filtering at all.
    # (Asserted with an explicit empty-ish param rather than a bare
    # request: `compute_distribution` is memoized per generation on its
    # filter dataclass, and a bare `AnalyticsFilters()` key is already
    # populated by other tests in this module/process.)
    everything = client.get(
        "/api/v1/analytics/distribution", params={"account_ids": [account.id]}
    ).json()
    assert Decimal(everything["total"]) == Decimal("95.00")


def test_income_category_always_included(client: TestClient, db_session: Session) -> None:
    """Unlike "Payments & Transfers", rows categorized as "Income" show up
    in every aggregate by default — only transfers are gated behind
    include_excluded."""
    account, batch = _make_batch(db_session)
    income = _seeded_category(db_session, "Income")
    transfers = _seeded_category(db_session, "Payments & Transfers")
    food = _seeded_category(db_session, "FOOD")

    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 10), amount="-30.00",
        description="TACOS", category=food, category_source="keyword", content_hash_suffix="1",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 15), amount="1000.00",
        description="PAYROLL", category=income, category_source="keyword", content_hash_suffix="2",
    )
    _make_txn(
        db_session, account, batch, txn_date=date(2026, 10, 20), amount="-500.00",
        description="AUTOPAY PAYMENT THANK YOU", category=transfers, category_source="transfer",
        content_hash_suffix="3",
    )
    db_session.commit()

    # date_from/date_to pin this call to its own cache key — plain
    # "/analytics/summary" with no params collides with the identical
    # no-param call in test_summary_excludes_transfers_by_default (the
    # in-process aggregate cache keys on (generation, *args), and the
    # per-test TRUNCATE/reseed fixture doesn't bump the generation).
    summary_resp = client.get(
        "/api/v1/analytics/summary", params={"date_from": "2026-10-01", "date_to": "2026-10-31"}
    )
    summary_body = summary_resp.json()
    assert Decimal(summary_body["total_in"]) == Decimal("1000.00")
    assert summary_body["transaction_count"] == 2  # food + income; transfer excluded

    dist_resp = client.get(
        "/api/v1/analytics/distribution", params={"date_from": "2026-10-01", "date_to": "2026-10-31"}
    )
    dist_names = {e["name"] for e in dist_resp.json()["entries"]}
    assert "Income" not in dist_names  # distribution sums outflows only
    assert "Payments & Transfers" not in dist_names


def test_timeseries_shape(client: TestClient, db_session: Session) -> None:
    _seed_standard_set(db_session)

    resp = client.get("/api/v1/analytics/timeseries", params={"granularity": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["granularity"] == "month"
    assert "2026-09" in body["periods"]
    assert "2026-10" in body["periods"]

    food_series = next(s for s in body["series"] if s["name"] == "FOOD")
    assert len(food_series["values"]) == len(body["periods"])
    by_period = {v["period"]: Decimal(v["value"]) for v in food_series["values"]}
    assert by_period["2026-09"] == Decimal("-20.00")
    assert by_period["2026-10"] == Decimal("-30.00")

    # Transfers excluded by default -> not present as a series at all.
    assert not any(s["name"] == "Payments & Transfers" for s in body["series"])


def test_timeseries_week_granularity_runs(client: TestClient, db_session: Session) -> None:
    _seed_standard_set(db_session)
    resp = client.get("/api/v1/analytics/timeseries", params={"granularity": "week"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["granularity"] == "week"
    assert len(body["periods"]) > 0


def test_analytics_date_range_filter(client: TestClient, db_session: Session) -> None:
    _seed_standard_set(db_session)

    resp = client.get(
        "/api/v1/analytics/summary",
        params={"date_from": "2026-10-01", "date_to": "2026-10-31"},
    )
    body = resp.json()
    assert Decimal(body["total_spent"]) == Decimal("30.00")
    assert body["transaction_count"] == 2
