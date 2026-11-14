"""Server-side cache for small pieces of UI state: the active theme and
each page's last-used filter selections. Single-user/local app, so one
row per `key` is enough — no auth/user scoping needed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import UserPreference
from app.schemas.preferences import PreferenceRead, PreferenceWrite

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get(
    "/{key}",
    response_model=PreferenceRead | None,
    summary="Get a persisted preference",
    description="Returns null if nothing has been stored under this key yet.",
)
def get_preference(key: str, db: Session = Depends(get_db)) -> PreferenceRead | None:
    pref = db.get(UserPreference, key)
    if pref is None:
        return None
    return PreferenceRead(key=pref.key, value=pref.value)


@router.put(
    "/{key}",
    response_model=PreferenceRead,
    summary="Set a persisted preference",
    description="Upserts the value under this key, replacing whatever was there.",
)
def put_preference(key: str, payload: PreferenceWrite, db: Session = Depends(get_db)) -> PreferenceRead:
    stmt = (
        pg_insert(UserPreference)
        .values(key=key, value=payload.value)
        .on_conflict_do_update(index_elements=["key"], set_={"value": payload.value})
    )
    db.execute(stmt)
    db.commit()
    return PreferenceRead(key=key, value=payload.value)
