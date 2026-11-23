"""API tests for the workspace lifecycle and, more importantly, for
isolation between workspaces.

The isolation tests are the point of this file. Every data endpoint
filters on the workspace resolved from `X-Workspace`, and a single
forgotten filter is a data leak rather than a visible bug — so these
assert the boundary from the outside, through HTTP, the same way a real
client would hit it.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Account, Category, Institution, Transaction, Workspace
from app.seed import INIT_SLUG

API = "/api/v1"


# --- helpers ---------------------------------------------------------------


def _create_workspace(unscoped_client: TestClient, slug: str, name: str | None = None):
    body: dict = {"slug": slug}
    if name is not None:
        body["name"] = name
    return unscoped_client.post(f"{API}/workspaces", json=body)


def _seed_txn(
    db_session: Session,
    workspace: Workspace,
    *,
    description: str,
    amount: str = "-10.00",
    hash_suffix: str = "a",
) -> Transaction:
    """Insert one transaction directly into `workspace`."""
    from app.models import IngestBatch

    institution = db_session.query(Institution).filter(Institution.code == "amex").one()
    account = Account(
        workspace_id=workspace.id,
        institution_id=institution.id,
        account_hint=f"hint-{workspace.id}",
        display_name=f"Acct {workspace.slug}",
        kind="card",
    )
    db_session.add(account)
    db_session.flush()

    batch = IngestBatch(
        workspace_id=workspace.id,
        filename="t.csv",
        institution_id=institution.id,
        account_id=account.id,
        file_sha256="0" * 64,
        row_count=1,
        status="completed",
    )
    db_session.add(batch)
    db_session.flush()

    txn = Transaction(
        workspace_id=workspace.id,
        account_id=account.id,
        batch_id=batch.id,
        txn_date=date(2026, 1, 15),
        posted_date=date(2026, 1, 15),
        description=description,
        normalized_description=description.upper(),
        amount=Decimal(amount),
        bank_category=None,
        category_id=None,
        category_source="default",
        content_hash=(hash_suffix * 64)[:64],
        occurrence_index=0,
        raw_row={"raw": description},
    )
    db_session.add(txn)
    db_session.commit()
    return txn


# --- the header guard ------------------------------------------------------


def test_missing_workspace_header_is_400(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/transactions")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "WORKSPACE_REQUIRED"


def test_unknown_workspace_header_is_404(unscoped_client: TestClient):
    response = unscoped_client.get(
        f"{API}/transactions", headers={"X-Workspace": "nope-does-not-exist"}
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WORKSPACE_NOT_FOUND"


def test_header_is_case_insensitive_on_the_slug(client: TestClient):
    """Slugs normalize to lowercase, so a capitalized header still works."""
    response = client.get(
        f"{API}/categories", headers={"X-Workspace": INIT_SLUG.upper()}
    )
    assert response.status_code == 200


# --- resolve / availability / create ---------------------------------------


def test_get_workspace_by_slug(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/workspaces/{INIT_SLUG}")
    assert response.status_code == 200
    assert response.json()["slug"] == INIT_SLUG


def test_get_unknown_workspace_404s(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/workspaces/not-a-workspace")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WORKSPACE_NOT_FOUND"


def test_availability_reports_taken_slug(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/workspaces/{INIT_SLUG}/availability")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "taken" in body["reason"].lower()


def test_availability_reports_free_slug(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/workspaces/brand-new-slug/availability")
    assert response.status_code == 200
    assert response.json() == {
        "slug": "brand-new-slug",
        "available": True,
        "reason": None,
    }


def test_availability_rejects_malformed_slug(unscoped_client: TestClient):
    response = unscoped_client.get(f"{API}/workspaces/Not A Slug!/availability")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "invalid" in body["reason"].lower()


def test_create_workspace_provisions_generic_defaults(
    unscoped_client: TestClient, db_session: Session
):
    response = _create_workspace(unscoped_client, "ada", "Ada's budget")
    assert response.status_code == 201
    body = response.json()
    assert body["slug"] == "ada"
    assert body["name"] == "Ada's budget"

    ws = db_session.query(Workspace).filter(Workspace.slug == "ada").one()
    categories = db_session.query(Category).filter(Category.workspace_id == ws.id).all()

    # The required system categories exist, so the categorizer can load.
    names = {c.name for c in categories}
    assert "Uncategorized" in names
    assert "Payments & Transfers" in names

    # And a budget is deliberately NOT created.
    bootstrap = unscoped_client.get(f"{API}/workspaces/ada/bootstrap").json()
    assert bootstrap["budget_expenses"] == []
    assert bootstrap["has_transactions"] is False


def test_create_workspace_does_not_leak_personal_keywords(
    unscoped_client: TestClient, db_session: Session
):
    """A new workspace must never inherit the `init` workspace's own
    merchant keywords — those belong to one person, not to a default."""
    from app.models import CategoryKeyword

    assert _create_workspace(unscoped_client, "fresh").status_code == 201
    ws = db_session.query(Workspace).filter(Workspace.slug == "fresh").one()

    personal = {
        "APPFOLIO",
        "MAGNIFY REAL EST",
        "PRUNEYARD CINEMAS",
        "LA VICTORIA SANTA",
        "GREAT WHITE MELROSE",
        "HOUSE OF BAGELS",
        "KIOSOFT",
        "DEPT EDUCATION STUDENT LN",
        "TOYOTA ACH RTL",
        "CRAP EYEWEAR",
        "MLB*SF GIANTS",
        "PGANDE",
        "SONIC.NET",
    }
    leaked = {
        k.keyword
        for k in db_session.query(CategoryKeyword)
        .filter(CategoryKeyword.workspace_id == ws.id)
        .all()
    } & personal
    assert leaked == set()


def test_create_duplicate_slug_is_409(unscoped_client: TestClient):
    assert _create_workspace(unscoped_client, "twice").status_code == 201
    response = _create_workspace(unscoped_client, "twice")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "WORKSPACE_TAKEN"


def test_create_normalizes_slug_case_and_whitespace(unscoped_client: TestClient):
    response = _create_workspace(unscoped_client, "  MixedCase  ")
    assert response.status_code == 201
    assert response.json()["slug"] == "mixedcase"


def test_create_rejects_malformed_slug(unscoped_client: TestClient):
    response = _create_workspace(unscoped_client, "has spaces")
    assert response.status_code == 422


def test_create_defaults_name_to_slug(unscoped_client: TestClient):
    response = _create_workspace(unscoped_client, "nameless")
    assert response.status_code == 201
    assert response.json()["name"] == "nameless"


# --- bootstrap -------------------------------------------------------------


def test_bootstrap_returns_everything_in_one_call(client: TestClient):
    response = client.get(f"{API}/workspaces/{INIT_SLUG}/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["slug"] == INIT_SLUG
    # The seeded workspace always has categories and buckets.
    assert len(body["categories"]) > 0
    assert len(body["buckets"]) > 0
    for key in ("accounts", "budget_expenses", "has_transactions", "transaction_count"):
        assert key in body


def test_bootstrap_has_transactions_flips_after_a_transaction_exists(
    unscoped_client: TestClient, db_session: Session
):
    assert _create_workspace(unscoped_client, "gated").status_code == 201
    ws = db_session.query(Workspace).filter(Workspace.slug == "gated").one()

    before = unscoped_client.get(f"{API}/workspaces/gated/bootstrap").json()
    assert before["has_transactions"] is False
    assert before["transaction_count"] == 0

    _seed_txn(db_session, ws, description="COFFEE", hash_suffix="b")

    after = unscoped_client.get(f"{API}/workspaces/gated/bootstrap").json()
    assert after["has_transactions"] is True
    assert after["transaction_count"] == 1


# --- isolation (the important part) ----------------------------------------


def test_transactions_are_isolated_between_workspaces(
    unscoped_client: TestClient, db_session: Session
):
    assert _create_workspace(unscoped_client, "alpha").status_code == 201
    assert _create_workspace(unscoped_client, "beta").status_code == 201
    alpha = db_session.query(Workspace).filter(Workspace.slug == "alpha").one()
    beta = db_session.query(Workspace).filter(Workspace.slug == "beta").one()

    _seed_txn(db_session, alpha, description="ALPHA COFFEE", hash_suffix="c")
    _seed_txn(db_session, beta, description="BETA GROCERY", hash_suffix="d")

    alpha_rows = unscoped_client.get(
        f"{API}/transactions", headers={"X-Workspace": "alpha"}
    ).json()["items"]
    beta_rows = unscoped_client.get(
        f"{API}/transactions", headers={"X-Workspace": "beta"}
    ).json()["items"]

    assert [r["description"] for r in alpha_rows] == ["ALPHA COFFEE"]
    assert [r["description"] for r in beta_rows] == ["BETA GROCERY"]


def test_same_category_name_can_exist_in_two_workspaces(
    unscoped_client: TestClient
):
    """`categories.name` used to be globally unique, which would make
    this 409. It is now unique per workspace."""
    assert _create_workspace(unscoped_client, "ws1").status_code == 201
    assert _create_workspace(unscoped_client, "ws2").status_code == 201

    first = unscoped_client.post(
        f"{API}/categories",
        json={"name": "Hobby Shop"},
        headers={"X-Workspace": "ws1"},
    )
    second = unscoped_client.post(
        f"{API}/categories",
        json={"name": "Hobby Shop"},
        headers={"X-Workspace": "ws2"},
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]


def test_same_keyword_can_exist_in_two_workspaces(unscoped_client: TestClient):
    """`category_keywords.keyword` was globally unique too."""
    assert _create_workspace(unscoped_client, "kw1").status_code == 201
    assert _create_workspace(unscoped_client, "kw2").status_code == 201

    created = []
    for slug in ("kw1", "kw2"):
        cat = unscoped_client.post(
            f"{API}/categories", json={"name": "Niche"}, headers={"X-Workspace": slug}
        ).json()
        response = unscoped_client.post(
            f"{API}/categories/{cat['id']}/keywords",
            json={"keyword": "SHARED-MERCHANT", "apply_to_existing": False},
            headers={"X-Workspace": slug},
        )
        assert response.status_code == 201, response.text
        created.append(response.json()["keyword"]["keyword"])

    assert created == ["SHARED-MERCHANT", "SHARED-MERCHANT"]


def test_same_bucket_name_can_exist_in_two_workspaces(unscoped_client: TestClient):
    assert _create_workspace(unscoped_client, "bk1").status_code == 201
    assert _create_workspace(unscoped_client, "bk2").status_code == 201

    for slug in ("bk1", "bk2"):
        response = unscoped_client.post(
            f"{API}/buckets", json={"name": "Hobbies"}, headers={"X-Workspace": slug}
        )
        assert response.status_code == 201, response.text


def test_categories_from_another_workspace_are_not_visible(
    unscoped_client: TestClient
):
    assert _create_workspace(unscoped_client, "seer").status_code == 201
    assert _create_workspace(unscoped_client, "hidden").status_code == 201

    unscoped_client.post(
        f"{API}/categories",
        json={"name": "Very Secret Category"},
        headers={"X-Workspace": "hidden"},
    )

    names = {
        c["name"]
        for c in unscoped_client.get(
            f"{API}/categories", headers={"X-Workspace": "seer"}
        ).json()
    }
    assert "Very Secret Category" not in names


def test_cannot_patch_a_category_in_another_workspace(unscoped_client: TestClient):
    assert _create_workspace(unscoped_client, "owner").status_code == 201
    assert _create_workspace(unscoped_client, "attacker").status_code == 201

    victim = unscoped_client.post(
        f"{API}/categories",
        json={"name": "Owned"},
        headers={"X-Workspace": "owner"},
    ).json()

    response = unscoped_client.patch(
        f"{API}/categories/{victim['id']}",
        json={"name": "Renamed By Someone Else"},
        headers={"X-Workspace": "attacker"},
    )
    assert response.status_code == 404


def test_cannot_bulk_recategorize_another_workspaces_transactions(
    unscoped_client: TestClient, db_session: Session
):
    """The bulk endpoint takes transaction ids straight from the request
    body, so it has to filter on the workspace as well as the ids."""
    assert _create_workspace(unscoped_client, "victim").status_code == 201
    assert _create_workspace(unscoped_client, "thief").status_code == 201
    victim_ws = db_session.query(Workspace).filter(Workspace.slug == "victim").one()

    txn = _seed_txn(db_session, victim_ws, description="VICTIM ROW", hash_suffix="e")
    original_category_id = txn.category_id

    thief_category = unscoped_client.post(
        f"{API}/categories",
        json={"name": "Thief Target"},
        headers={"X-Workspace": "thief"},
    ).json()

    response = unscoped_client.post(
        f"{API}/transactions/bulk-recategorize",
        json={"transaction_ids": [txn.id], "category_id": thief_category["id"]},
        headers={"X-Workspace": "thief"},
    )
    # The call "succeeds" but must have matched nothing.
    assert response.status_code == 200
    assert response.json()["affected_count"] == 0

    db_session.expire_all()
    reloaded = db_session.get(Transaction, txn.id)
    assert reloaded.category_id == original_category_id


def test_cannot_patch_a_transaction_in_another_workspace(
    unscoped_client: TestClient, db_session: Session
):
    assert _create_workspace(unscoped_client, "tv").status_code == 201
    assert _create_workspace(unscoped_client, "tt").status_code == 201
    victim_ws = db_session.query(Workspace).filter(Workspace.slug == "tv").one()
    txn = _seed_txn(db_session, victim_ws, description="PATCH ME", hash_suffix="f")

    response = unscoped_client.patch(
        f"{API}/transactions/{txn.id}",
        json={"is_recurring": True},
        headers={"X-Workspace": "tt"},
    )
    assert response.status_code == 404


def test_analytics_are_isolated_between_workspaces(
    unscoped_client: TestClient, db_session: Session
):
    """The analytics cache is keyed on the filter object alone, so the
    workspace has to be part of those filters or one workspace would be
    served the other's cached totals."""
    assert _create_workspace(unscoped_client, "an1").status_code == 201
    assert _create_workspace(unscoped_client, "an2").status_code == 201
    ws1 = db_session.query(Workspace).filter(Workspace.slug == "an1").one()
    ws2 = db_session.query(Workspace).filter(Workspace.slug == "an2").one()

    _seed_txn(db_session, ws1, description="SPEND ONE", amount="-100.00", hash_suffix="1")
    _seed_txn(db_session, ws2, description="SPEND TWO", amount="-7.00", hash_suffix="2")

    one = unscoped_client.get(
        f"{API}/analytics/summary", headers={"X-Workspace": "an1"}
    ).json()
    two = unscoped_client.get(
        f"{API}/analytics/summary", headers={"X-Workspace": "an2"}
    ).json()

    assert Decimal(str(one["total_spent"])) == Decimal("100.00")
    assert Decimal(str(two["total_spent"])) == Decimal("7.00")


def test_preferences_are_isolated_between_workspaces(unscoped_client: TestClient):
    assert _create_workspace(unscoped_client, "pf1").status_code == 201
    assert _create_workspace(unscoped_client, "pf2").status_code == 201

    unscoped_client.put(
        f"{API}/preferences/theme",
        json={"value": {"mode": "dark"}},
        headers={"X-Workspace": "pf1"},
    )

    other = unscoped_client.get(
        f"{API}/preferences/theme", headers={"X-Workspace": "pf2"}
    )
    assert other.status_code == 200
    assert other.json() is None

    mine = unscoped_client.get(
        f"{API}/preferences/theme", headers={"X-Workspace": "pf1"}
    ).json()
    assert mine["value"] == {"mode": "dark"}


def test_audit_history_is_isolated_between_workspaces(unscoped_client: TestClient):
    assert _create_workspace(unscoped_client, "au1").status_code == 201
    assert _create_workspace(unscoped_client, "au2").status_code == 201

    unscoped_client.post(
        f"{API}/categories",
        json={"name": "Audit Me"},
        headers={"X-Workspace": "au1"},
    )

    other_events = unscoped_client.get(
        f"{API}/audit", headers={"X-Workspace": "au2"}
    ).json()
    assert other_events["total"] == 0

    own_events = unscoped_client.get(
        f"{API}/audit", headers={"X-Workspace": "au1"}
    ).json()
    assert own_events["total"] >= 1


def test_two_workspaces_can_ingest_the_same_csv(unscoped_client: TestClient):
    """The regression this schema change exists for.

    `content_hash` is derived from the statement's contents alone, so the
    same file hashes identically in every workspace. With the workspace
    missing from `uq_transactions_hash_occurrence`, the second
    workspace's rows would all be silently discarded as duplicates.
    """
    from pathlib import Path

    csv_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "transactions"
        / "amex_90_day.csv"
    )
    assert csv_path.exists(), f"missing sample file: {csv_path}"

    assert _create_workspace(unscoped_client, "ing1").status_code == 201
    assert _create_workspace(unscoped_client, "ing2").status_code == 201

    results = {}
    for slug in ("ing1", "ing2"):
        with csv_path.open("rb") as handle:
            response = unscoped_client.post(
                f"{API}/uploads",
                files={"file": (csv_path.name, handle, "text/csv")},
                headers={"X-Workspace": slug},
            )
        assert response.status_code == 201, response.text
        results[slug] = response.json()["counts"]

    # Both workspaces ingest the full file; neither dedupes against the other.
    assert results["ing1"]["inserted"] == 105, results["ing1"]
    assert results["ing2"]["inserted"] == 105, results["ing2"]
    assert results["ing1"]["duplicates"] == 0
    assert results["ing2"]["duplicates"] == 0

    # Re-uploading into the same workspace still dedupes, as before.
    with csv_path.open("rb") as handle:
        again = unscoped_client.post(
            f"{API}/uploads",
            files={"file": (csv_path.name, handle, "text/csv")},
            headers={"X-Workspace": "ing1"},
        )
    assert again.status_code == 201
    assert again.json()["counts"]["inserted"] == 0
    assert again.json()["counts"]["duplicates"] == 105


def test_each_workspace_gets_its_own_account_rows(unscoped_client: TestClient):
    """Accounts are per-workspace even though institutions are global."""
    from pathlib import Path

    csv_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "transactions"
        / "amex_90_day.csv"
    )
    assert _create_workspace(unscoped_client, "acc1").status_code == 201
    assert _create_workspace(unscoped_client, "acc2").status_code == 201

    for slug in ("acc1", "acc2"):
        with csv_path.open("rb") as handle:
            unscoped_client.post(
                f"{API}/uploads",
                files={"file": (csv_path.name, handle, "text/csv")},
                headers={"X-Workspace": slug},
            )

    one = unscoped_client.get(f"{API}/accounts", headers={"X-Workspace": "acc1"}).json()
    two = unscoped_client.get(f"{API}/accounts", headers={"X-Workspace": "acc2"}).json()

    # This file spans two Amex cards, so each workspace discovers both —
    # and sees only its own copies, never the other workspace's.
    assert len(one) == len(two) == 2
    assert {a["account_hint"] for a in one} == {a["account_hint"] for a in two}
    assert {a["institution_code"] for a in one} == {"amex"}
    assert {a["id"] for a in one}.isdisjoint({a["id"] for a in two})

    # Counts are per-workspace, not the combined total across both.
    assert sum(a["transaction_count"] for a in one) == 105
    assert sum(a["transaction_count"] for a in two) == 105


def test_deleting_a_workspaces_category_does_not_suppress_it_elsewhere(
    unscoped_client: TestClient, db_session: Session
):
    """Seed tombstones are per-workspace: one workspace deleting a
    category must not stop another from having it."""
    from app.models import SeedSuppression

    assert _create_workspace(unscoped_client, "sup1").status_code == 201
    ws1 = db_session.query(Workspace).filter(Workspace.slug == "sup1").one()

    created = unscoped_client.post(
        f"{API}/categories", json={"name": "Doomed"}, headers={"X-Workspace": "sup1"}
    ).json()
    unscoped_client.delete(
        f"{API}/categories/{created['id']}", headers={"X-Workspace": "sup1"}
    )

    tombstones = (
        db_session.query(SeedSuppression)
        .filter(SeedSuppression.name == "Doomed")
        .all()
    )
    assert len(tombstones) == 1
    assert tombstones[0].workspace_id == ws1.id
