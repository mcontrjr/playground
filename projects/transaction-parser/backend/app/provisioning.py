"""Default configuration handed to a brand-new workspace.

This is deliberately separate from `app.seed`. That seeder keeps *one*
long-lived workspace (`init`) in sync with a hardcoded personal category
list on every backend restart, tombstones and all — and that list is
nobody's default. Provisioning runs exactly once, at create time, and
then never touches the workspace again; whatever the user does to these
rows afterwards is theirs.

The defaults here are generic by construction: the same buckets, but
categories and keywords that describe spending in general rather than one
person's merchants. Nothing like APPFOLIO or PRUNEYARD CINEMAS belongs in
someone else's fresh workspace. No budget lines are created at all — the
Budget page starts empty so the user sets their own targets.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import Bucket, Category, CategoryKeyword, Workspace

logger = logging.getLogger("provisioning")

#: Same coarse groupings the app has always used. OTHER is the
#: undeletable fallback every uncategorized category lands in.
BUCKET_NAMES: list[str] = [
    "ESSENTIALS",
    "LIFESTYLE",
    "INCOME",
    "TRANSFERS",
    "SAVINGS",
    "OTHER",
]

#: Ordered — index becomes `priority`, so earlier entries match first.
#: Keywords are broad and brand-neutral; a few unambiguous national
#: brands are included where the brand *is* the category signal on a
#: statement line (NETFLIX, UBER), but nothing regional or personal.
DEFAULT_CATEGORIES: list[dict] = [
    {
        "name": "Rent",
        "group": "ESSENTIALS",
        "keywords": ["RENT", "PROPERTY MANAGEMENT", "LEASING"],
    },
    {
        "name": "Utilities",
        "group": "ESSENTIALS",
        "keywords": ["UTILITY", "ELECTRIC", "WATER", "GAS COMPANY", "POWER"],
    },
    {
        "name": "Internet & Phone",
        "group": "ESSENTIALS",
        "keywords": ["INTERNET", "WIRELESS", "MOBILE", "BROADBAND", "CABLE"],
    },
    {
        "name": "Groceries",
        "group": "ESSENTIALS",
        "keywords": ["GROCERY", "SUPERMARKET", "MARKET", "FOODS"],
    },
    {
        "name": "Gas & Fuel",
        "group": "ESSENTIALS",
        "keywords": ["GAS", "FUEL", "GASOLINE"],
    },
    {
        "name": "Insurance",
        "group": "ESSENTIALS",
        "keywords": ["INSURANCE", "INS PREM"],
    },
    {
        "name": "Pharmacy & Health",
        "group": "ESSENTIALS",
        "keywords": ["PHARMACY", "DENTAL", "MEDICAL", "CLINIC", "DOCTOR"],
    },
    {
        "name": "Loans",
        "group": "ESSENTIALS",
        "keywords": ["LOAN", "STUDENT LN", "MORTGAGE"],
    },
    {
        "name": "Dining & Coffee",
        "group": "LIFESTYLE",
        "keywords": ["RESTAURANT", "CAFE", "COFFEE", "PIZZA", "BURGER", "BAR & GRILL"],
    },
    {
        "name": "Food Delivery",
        "group": "LIFESTYLE",
        "keywords": ["DOORDASH", "UBER EATS", "GRUBHUB", "INSTACART"],
    },
    {
        "name": "Transportation",
        "group": "LIFESTYLE",
        "keywords": ["UBER", "LYFT", "TRANSIT", "PARKING", "TOLL"],
    },
    {
        "name": "Travel",
        "group": "LIFESTYLE",
        "keywords": ["AIRLINE", "HOTEL", "RENTAL CAR", "AIR", "RESORT"],
    },
    {
        "name": "Shopping",
        "group": "LIFESTYLE",
        "keywords": ["AMAZON", "STORE", "RETAIL", "CLOTHING"],
    },
    {
        "name": "Streaming & Subscriptions",
        "group": "LIFESTYLE",
        "keywords": ["NETFLIX", "SPOTIFY", "HULU", "SUBSCRIPTION", "PRIME VIDEO"],
    },
    {
        "name": "Fitness",
        "group": "LIFESTYLE",
        "keywords": ["GYM", "FITNESS", "YOGA"],
    },
    {
        "name": "Entertainment",
        "group": "LIFESTYLE",
        "keywords": ["CINEMA", "THEATRE", "MUSEUM", "TICKETS"],
    },
    {
        "name": "Home & Hardware",
        "group": "LIFESTYLE",
        "keywords": ["HARDWARE", "HOME IMPROVEMENT", "FURNITURE"],
    },
    {
        "name": "Fees & Interest",
        "group": "OTHER",
        "keywords": ["FEE", "INTEREST CHARGE", "SERVICE CHARGE", "LATE FEE"],
    },
    {
        "name": "ATM & Cash",
        "group": "OTHER",
        "keywords": ["ATM", "CASH WITHDRAWAL"],
    },
    # --- system / excluded-from-analytics tail -----------------------------
    {
        "name": "Income",
        "group": "INCOME",
        "keywords": ["PAYROLL", "DIRECT DEP", "ELECTRONIC DEPOSIT", "SALARY"],
        "excluded_from_analytics": True,
    },
    {
        "name": "Savings",
        "group": "SAVINGS",
        "keywords": [],
    },
    {
        "name": "Payments & Transfers",
        "group": "TRANSFERS",
        "keywords": [
            "AUTOPAY", "EPAYMENT", "ONLINE PAYMENT", "THANK YOU",
            "PYMT", "PMT", "TRANSFER",
        ],
        "is_system": True,
        "excluded_from_analytics": True,
    },
    {
        "name": "Uncategorized",
        "group": "OTHER",
        "keywords": [],
        "is_system": True,
    },
]


def provision_workspace(db: Session, workspace: Workspace) -> None:
    """Create the default buckets, categories and keywords for a new
    workspace. Flushes but does not commit — the caller owns the
    transaction.

    Assumes the workspace is empty; this is only ever called straight
    after creating the row, so there is no get-or-create dance and no
    tombstone handling (there is nothing yet for a user to have deleted).
    """
    buckets: dict[str, Bucket] = {}
    for name in BUCKET_NAMES:
        bucket = Bucket(workspace_id=workspace.id, name=name)
        db.add(bucket)
        buckets[name] = bucket
    db.flush()

    # One keyword can only belong to one category per workspace, and
    # earlier entries win — same precedence rule the categorizer applies.
    claimed: set[str] = set()

    for priority, entry in enumerate(DEFAULT_CATEGORIES):
        category = Category(
            workspace_id=workspace.id,
            name=entry["name"],
            is_system=entry.get("is_system", False),
            excluded_from_analytics=entry.get("excluded_from_analytics", False),
            priority=priority,
            bucket_id=buckets[entry["group"]].id,
        )
        db.add(category)
        db.flush()

        for raw in entry["keywords"]:
            kw = raw.upper().strip()
            if not kw or kw in claimed:
                continue
            claimed.add(kw)
            db.add(
                CategoryKeyword(
                    workspace_id=workspace.id,
                    category_id=category.id,
                    keyword=kw,
                )
            )

    db.flush()
    logger.info(
        "provisioned workspace %r: %d buckets, %d categories",
        workspace.slug,
        len(BUCKET_NAMES),
        len(DEFAULT_CATEGORIES),
    )
