"""Shared FastAPI dependencies.

`get_workspace` is the single place a request's tenant is resolved. Every
data-bearing router depends on it, and every query in `app.api` /
`app.services` filters on the workspace it returns — that filter is the
only thing separating one user's records from another's, so a query that
forgets it is a data leak, not just a bug.

The workspace travels in the `X-Workspace` header rather than the URL
path: the frontend sets it once in its fetch wrapper, which keeps all
~25 existing query hooks and every router prefix unchanged.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Workspace

WORKSPACE_HEADER = "X-Workspace"


def get_workspace(
    x_workspace: str | None = Header(
        default=None,
        alias=WORKSPACE_HEADER,
        description="Slug of the workspace this request operates on.",
    ),
    db: Session = Depends(get_db),
) -> Workspace:
    """Resolve the `X-Workspace` header to a Workspace row.

    Raises 400 when the header is absent (the client is misconfigured)
    and 404 when the slug is unknown (the workspace was deleted, or the
    user mistyped it on the splash screen) — the frontend distinguishes
    these to decide whether to show an error or bounce back to splash.
    """
    if not x_workspace or not x_workspace.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "WORKSPACE_REQUIRED",
                "message": f"Missing required {WORKSPACE_HEADER} header.",
            },
        )

    slug = x_workspace.strip().lower()
    workspace = db.scalar(select(Workspace).where(Workspace.slug == slug))
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WORKSPACE_NOT_FOUND",
                "message": f"No workspace with slug {slug!r}.",
            },
        )
    return workspace
