"""API test fixtures: a real, dedicated Postgres test database.

Connects to the same Postgres server the dev stack uses (localhost,
the host-mapped port from `.env` / docker-compose, default 55432), as
the same user, but against a separate `transaction_parser_test`
database so these tests never touch (or truncate) the dev data that
Phase 3's manual verification step deliberately leaves behind.

Session-scoped setup: create the test database if missing, run
`alembic upgrade head` against it, then run the seed script once.
Function-scoped: truncate all tables (cascade, restart identity)
before each test for isolation, and override the app's `get_db`
dependency to hand out sessions bound to the test database.
"""
from __future__ import annotations

import os
import pathlib
from collections.abc import Generator

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

PG_HOST = os.environ.get("TEST_PG_HOST", "localhost")
PG_PORT = int(os.environ.get("TEST_PG_PORT", "55432"))
PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
TEST_DB_NAME = "transaction_parser_test"

TEST_DATABASE_URL = (
    f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{TEST_DB_NAME}"
)

# All app imports must happen *after* DATABASE_URL is pointed at the test
# database, since app.db builds its engine at import time from app.config.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.seed import INIT_SLUG  # noqa: E402 — must follow the env var above


def _create_database_if_missing() -> None:
    admin_conn = psycopg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, dbname="postgres"
    )
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        admin_conn.close()


def _run_migrations() -> None:
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> Generator[None, None, None]:
    _create_database_if_missing()
    _run_migrations()

    # Import and run the seed script against the (now migrated) test DB.
    from app import seed as seed_module

    seed_module.run()

    yield


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, future=True)
    yield engine
    engine.dispose()


_TABLES_TO_TRUNCATE = (
    "parse_failures",
    "transactions",
    "ingest_batches",
    "accounts",
    # institutions are immutable reference data, left intact.
    # categories/category_keywords/buckets/audit_events ARE truncated below
    # (re-seeded after) since Phase 2/4 tests mutate them directly (CRUD,
    # keyword add/remove, bucket CRUD, audit trail assertions) and each
    # test should start from the same known seeded state. buckets must be
    # included in the same CASCADE truncate as categories since
    # categories.bucket_id FKs into it. budget_expenses/
    # budget_expense_categories are test-created only (nothing seeds them),
    # but CASCADE-truncating them here keeps budget tests isolated too.
    "categories",
    "category_keywords",
    "buckets",
    "audit_events",
    "budget_expenses",
    "budget_expense_categories",
    # seed_suppressions must be truncated alongside categories: a tombstone
    # left behind from a previous test's delete would make the re-seed below
    # skip that category, so the next test would not start from the known
    # seeded state. Delete-tests assert on the tombstones they create.
    "seed_suppressions",
    # `workspaces` is deliberately NOT truncated: every table above FKs
    # into it with ON DELETE CASCADE, so truncating it would wipe the
    # seeded workspace and the re-seed would create a new one with a
    # different id on every test. The seed's get-or-create keeps the same
    # `init` row across the whole session instead.
)


@pytest.fixture(autouse=True)
def _truncate_between_tests(test_engine, _test_database) -> Generator[None, None, None]:
    yield
    with test_engine.begin() as conn:
        tables = ", ".join(_TABLES_TO_TRUNCATE)
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
        # Workspaces created by a test are dropped, but `init` survives:
        # truncating the table outright would cascade away the seeded
        # workspace and give it a new id on every re-seed.
        conn.execute(
            text("DELETE FROM workspaces WHERE slug <> :keep"), {"keep": INIT_SLUG}
        )

    from app import seed as seed_module

    seed_module.run()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def workspace(db_session):
    """The seeded `init` workspace every API test operates in."""
    from sqlalchemy import select

    from app.models import Workspace

    ws = db_session.scalar(select(Workspace).where(Workspace.slug == INIT_SLUG))
    assert ws is not None, "seed should have created the init workspace"
    return ws


@pytest.fixture
def client(test_engine) -> Generator[TestClient, None, None]:
    """TestClient that sends `X-Workspace` on every request.

    Setting it as a default header (rather than per call) keeps the
    existing tests untouched: they were written against a single
    implicit workspace, which is exactly what `init` now is.
    """
    from app.db import get_db
    from app.main import app

    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, headers={"X-Workspace": INIT_SLUG}) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def unscoped_client(test_engine) -> Generator[TestClient, None, None]:
    """TestClient with no `X-Workspace` header, for testing the guard
    itself and the workspace lifecycle endpoints."""
    from app.db import get_db
    from app.main import app

    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
