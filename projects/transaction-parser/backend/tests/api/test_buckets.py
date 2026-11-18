"""API tests for bucket CRUD: uppercase normalization, duplicate
conflicts, OTHER protection, category reassignment on delete, and
category_count."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Bucket, Category


def _seeded_bucket(db_session: Session, name: str) -> Bucket:
    return db_session.query(Bucket).filter(Bucket.name == name).one()


def test_list_buckets_includes_category_count(client: TestClient, db_session: Session) -> None:
    resp = client.get("/api/v1/buckets")
    assert resp.status_code == 200
    buckets = {b["name"]: b for b in resp.json()}
    assert "OTHER" in buckets
    assert "LIFESTYLE" in buckets
    # FOOD lives in LIFESTYLE per seed data.
    assert buckets["LIFESTYLE"]["category_count"] >= 1


def test_create_bucket_uppercases_name(client: TestClient) -> None:
    resp = client.post("/api/v1/buckets", json={"name": "  hobbies  "})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "HOBBIES"
    assert body["category_count"] == 0


def test_create_bucket_duplicate_name_409(client: TestClient) -> None:
    first = client.post("/api/v1/buckets", json={"name": "Side Projects"})
    assert first.status_code == 201
    conflict = client.post("/api/v1/buckets", json={"name": "side projects"})
    assert conflict.status_code == 409


def test_rename_bucket(client: TestClient) -> None:
    created = client.post("/api/v1/buckets", json={"name": "Temp"})
    bucket_id = created.json()["id"]

    resp = client.patch(f"/api/v1/buckets/{bucket_id}", json={"name": "renamed bucket"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "RENAMED BUCKET"


def test_rename_bucket_duplicate_name_409(client: TestClient) -> None:
    client.post("/api/v1/buckets", json={"name": "Keep"})
    created = client.post("/api/v1/buckets", json={"name": "Rename Me"})
    bucket_id = created.json()["id"]

    resp = client.patch(f"/api/v1/buckets/{bucket_id}", json={"name": "keep"})
    assert resp.status_code == 409


def test_other_bucket_cannot_be_renamed(client: TestClient, db_session: Session) -> None:
    other = _seeded_bucket(db_session, "OTHER")
    resp = client.patch(f"/api/v1/buckets/{other.id}", json={"name": "NOT OTHER"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "OTHER_BUCKET_PROTECTED"


def test_other_bucket_cannot_be_deleted(client: TestClient, db_session: Session) -> None:
    other = _seeded_bucket(db_session, "OTHER")
    resp = client.delete(f"/api/v1/buckets/{other.id}")
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "OTHER_BUCKET_PROTECTED"


def test_delete_bucket_defaults_reassignment_to_other(
    client: TestClient, db_session: Session
) -> None:
    other = _seeded_bucket(db_session, "OTHER")
    created = client.post("/api/v1/buckets", json={"name": "Scratch"})
    bucket_id = created.json()["id"]

    cat_resp = client.post(
        "/api/v1/categories", json={"name": "Scratch Category", "bucket_id": bucket_id}
    )
    assert cat_resp.status_code == 201
    category_id = cat_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/buckets/{bucket_id}")
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["moved_category_count"] == 1
    assert body["reassigned_to_bucket_id"] == other.id

    db_session.expire_all()
    category = db_session.get(Category, category_id)
    assert category.bucket_id == other.id


def test_delete_bucket_with_explicit_reassign_target(
    client: TestClient, db_session: Session
) -> None:
    source = client.post("/api/v1/buckets", json={"name": "Source Bucket"}).json()
    target = client.post("/api/v1/buckets", json={"name": "Target Bucket"}).json()

    cat_resp = client.post(
        "/api/v1/categories", json={"name": "Moved Category", "bucket_id": source["id"]}
    )
    category_id = cat_resp.json()["id"]

    del_resp = client.delete(
        f"/api/v1/buckets/{source['id']}",
        params={"reassign_to_bucket_id": target["id"]},
    )
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["moved_category_count"] == 1
    assert body["reassigned_to_bucket_id"] == target["id"]

    db_session.expire_all()
    category = db_session.get(Category, category_id)
    assert category.bucket_id == target["id"]


def test_delete_bucket_reassign_target_equals_source_400(client: TestClient) -> None:
    created = client.post("/api/v1/buckets", json={"name": "Self Target"}).json()
    resp = client.delete(
        f"/api/v1/buckets/{created['id']}",
        params={"reassign_to_bucket_id": created["id"]},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "REASSIGN_TARGET_IS_SOURCE"
