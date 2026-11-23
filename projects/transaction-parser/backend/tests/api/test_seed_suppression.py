"""Deleting a seeded category/keyword must survive the next seed run.

`app.seed` runs on every backend start and is get-or-create by name, so
before seed_suppressions existed an absent row was indistinguishable from
a never-seeded one: every restart recreated the categories and keywords
the user had deleted through the UI. These tests re-run the seeder in
process — exactly what a container restart does — and assert the deletion
holds.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import seed as seed_module
from app.models import Category, CategoryKeyword, SeedSuppression


def _reseed(db_session: Session) -> None:
    """Re-run the seeder the way a backend restart does, then resync."""
    db_session.commit()
    seed_module.run()
    db_session.expire_all()


def _category(db_session: Session, name: str) -> Category | None:
    return db_session.query(Category).filter(Category.name == name).one_or_none()


def _keyword(db_session: Session, keyword: str) -> CategoryKeyword | None:
    return (
        db_session.query(CategoryKeyword)
        .filter(CategoryKeyword.keyword == keyword)
        .one_or_none()
    )


def test_deleted_seeded_category_stays_deleted_after_reseed(
    client: TestClient, db_session: Session
) -> None:
    gym = _category(db_session, "GYM")
    assert gym is not None, "GYM is a seeded category"

    assert client.delete(f"/api/v1/categories/{gym.id}").status_code == 200
    db_session.expire_all()
    assert _category(db_session, "GYM") is None

    _reseed(db_session)

    assert _category(db_session, "GYM") is None, "seeder resurrected a deleted category"


def test_deleted_category_tombstones_its_keywords_too(
    client: TestClient, db_session: Session
) -> None:
    gym = _category(db_session, "GYM")
    assert gym is not None
    # MOVEMENT is seeded onto GYM and cascades away with it.
    assert _keyword(db_session, "MOVEMENT") is not None

    assert client.delete(f"/api/v1/categories/{gym.id}").status_code == 200
    _reseed(db_session)

    assert _keyword(db_session, "MOVEMENT") is None, (
        "a cascaded keyword came back on the next seed run"
    )


def test_removed_keyword_stays_removed_after_reseed(
    client: TestClient, db_session: Session
) -> None:
    gym = _category(db_session, "GYM")
    assert gym is not None
    movement = _keyword(db_session, "MOVEMENT")
    assert movement is not None

    response = client.delete(f"/api/v1/categories/{gym.id}/keywords/{movement.id}")
    assert response.status_code == 200
    db_session.expire_all()
    assert _keyword(db_session, "MOVEMENT") is None

    _reseed(db_session)

    assert _keyword(db_session, "MOVEMENT") is None, "seeder re-added a removed keyword"
    # The category itself was not deleted, so it must still be here.
    assert _category(db_session, "GYM") is not None


def test_recreating_a_deleted_category_clears_its_tombstone(
    client: TestClient, db_session: Session
) -> None:
    gym = _category(db_session, "GYM")
    assert gym is not None
    assert client.delete(f"/api/v1/categories/{gym.id}").status_code == 200
    db_session.expire_all()

    created = client.post("/api/v1/categories", json={"name": "GYM"})
    assert created.status_code == 201
    db_session.expire_all()

    tombstone = (
        db_session.query(SeedSuppression)
        .filter(SeedSuppression.kind == "category", SeedSuppression.name == "GYM")
        .one_or_none()
    )
    assert tombstone is None, "re-creating the category left its tombstone behind"

    _reseed(db_session)
    assert _category(db_session, "GYM") is not None, "user-recreated category vanished"


def test_reseed_leaves_untouched_seeded_data_alone(
    client: TestClient, db_session: Session
) -> None:
    """The suppression check must not make the seeder a no-op generally."""
    before = db_session.query(Category).count()
    assert before > 0

    _reseed(db_session)

    assert db_session.query(Category).count() == before
    assert _category(db_session, "GAS") is not None


def test_bucket_move_is_not_reverted_by_reseed(
    client: TestClient, db_session: Session
) -> None:
    """Seeding used to re-sync bucket_id to the plan on every run, undoing
    any bucket change the user made through the UI."""
    gym = _category(db_session, "GYM")
    assert gym is not None
    original_bucket_id = gym.bucket_id

    other_bucket_id = (
        db_session.query(Category.bucket_id)
        .filter(Category.bucket_id != original_bucket_id)
        .first()
    )
    assert other_bucket_id is not None, "need a second bucket to move into"
    target = other_bucket_id[0]

    response = client.patch(f"/api/v1/categories/{gym.id}", json={"bucket_id": target})
    assert response.status_code == 200

    _reseed(db_session)

    moved = _category(db_session, "GYM")
    assert moved is not None
    assert moved.bucket_id == target, "seeder reverted the user's bucket move"
