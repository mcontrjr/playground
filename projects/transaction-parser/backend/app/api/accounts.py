"""Account listing and rename endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Account, Institution, Transaction
from app.schemas.accounts import AccountPatch, AccountRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get(
    "",
    response_model=list[AccountRead],
    summary="List accounts",
    description="All accounts discovered during ingest, with institution info and transaction counts.",
)
def list_accounts(db: Session = Depends(get_db)) -> list[AccountRead]:
    stmt = (
        select(
            Account,
            Institution.code.label("institution_code"),
            Institution.display_name.label("institution_name"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Institution, Account.institution_id == Institution.id)
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .group_by(Account.id, Institution.code, Institution.display_name)
        .order_by(Institution.display_name, Account.display_name)
    )
    rows = db.execute(stmt).all()
    return [
        AccountRead(
            id=row.Account.id,
            institution_code=row.institution_code,
            institution_name=row.institution_name,
            account_hint=row.Account.account_hint,
            display_name=row.Account.display_name,
            kind=row.Account.kind,
            transaction_count=row.transaction_count,
        )
        for row in rows
    ]


@router.patch(
    "/{account_id}",
    response_model=AccountRead,
    summary="Rename an account",
    description="Updates an account's display_name (e.g. to disambiguate two cards at the same institution).",
)
def patch_account(
    account_id: int,
    payload: AccountPatch,
    db: Session = Depends(get_db),
) -> AccountRead:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    account.display_name = payload.display_name
    db.commit()
    db.refresh(account)

    institution = account.institution
    transaction_count = db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.account_id == account.id)
    ).scalar_one()

    return AccountRead(
        id=account.id,
        institution_code=institution.code,
        institution_name=institution.display_name,
        account_hint=account.account_hint,
        display_name=account.display_name,
        kind=account.kind,
        transaction_count=transaction_count,
    )
