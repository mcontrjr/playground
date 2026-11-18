"""FastAPI application factory for the transaction-parser backend."""
from fastapi import APIRouter, FastAPI

from app.api import (
    accounts,
    analytics,
    audit,
    buckets,
    budgets,
    categories,
    failures,
    preferences,
    transactions,
    uploads,
)

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Liveness/readiness probe used by docker compose and operators.",
    },
    {
        "name": "uploads",
        "description": "CSV statement upload and ingest-batch inspection.",
    },
    {
        "name": "transactions",
        "description": "Browse, filter, and recategorize parsed transactions.",
    },
    {
        "name": "categories",
        "description": "Category CRUD, keyword management, and impact previews.",
    },
    {
        "name": "failures",
        "description": "Rows that failed to parse, for review and resolution.",
    },
    {
        "name": "analytics",
        "description": "Aggregated timeseries/distribution/summary views.",
    },
    {
        "name": "accounts",
        "description": "Accounts discovered during ingest; rename support.",
    },
    {
        "name": "preferences",
        "description": "Server-side cache of UI state: active theme and per-page filter selections.",
    },
    {
        "name": "buckets",
        "description": "Coarse category groupings; OTHER is the undeletable fallback bucket.",
    },
    {
        "name": "audit",
        "description": "Read-only audit trail of category/bucket/transaction mutations, for the History page.",
    },
    {
        "name": "budget",
        "description": "Monthly budget expenses: CRUD plus the month-scoped summary (auto-imported income, actual-vs-goal per expense).",
    },
]


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title="Transaction Parser API",
        description=(
            "Backend for ingesting bank/card CSV statements, deduplicating and "
            "categorizing transactions, and serving analytics for a personal "
            "finance dashboard."
        ),
        version="0.1.0",
        openapi_tags=TAGS_METADATA,
        contact={"name": "Transaction Parser", "url": "https://github.com"},
    )

    @app.get(
        "/health",
        tags=["health"],
        summary="Health check",
        description="Returns 200 with a simple status payload when the service is up.",
    )
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api_v1 = APIRouter(prefix="/api/v1")

    @api_v1.get(
        "/",
        tags=["health"],
        summary="API root",
        description="Simple marker endpoint confirming the versioned API is mounted.",
    )
    def api_root() -> dict[str, str]:
        return {"api": "v1", "status": "ok"}

    api_v1.include_router(uploads.router)
    api_v1.include_router(failures.router)
    api_v1.include_router(transactions.router)
    api_v1.include_router(categories.router)
    api_v1.include_router(analytics.router)
    api_v1.include_router(accounts.router)
    api_v1.include_router(preferences.router)
    api_v1.include_router(buckets.router)
    api_v1.include_router(audit.router)
    api_v1.include_router(budgets.router)

    app.include_router(api_v1)

    return app


app = create_app()
