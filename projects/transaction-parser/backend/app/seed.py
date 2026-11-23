"""Idempotent seed script: institutions, categories, and category keywords.

Safe to run on every startup (and does so, via docker-compose's backend
command). Uses INSERT-if-missing / get-or-create patterns throughout so
repeated runs never raise integrity errors and never change existing data
beyond filling in what's missing.

**Scope.** Institutions are global. Everything else here belongs to one
specific workspace — `INIT_SLUG` below, the original single-user data set
this app grew out of, adopted by the workspaces migration.

This category list is *not* a default. It is one particular person's
merchants (APPFOLIO, PRUNEYARD CINEMAS, LA VICTORIA SANTA) and must
never be handed to anyone else. New workspaces get the generic defaults
in `app.provisioning`, once, at create time. Keeping the two apart is
what lets this list go on being re-synced on every restart without
leaking into another workspace.

Category/keyword source of truth: the legacy hardcoded dict at
`/home/mcontr/repos/mcontr/server/src/config.py` (CATEGORY_KEYWORDS, line 38).
Dict order is preserved as ascending priority (lower = matched first, i.e.
first key in the dict gets priority 0, and so on). Two legacy categories are
folded into the plan's system categories instead of being duplicated:

- PAYMENT (PYMT, PAYMENT, PMT) -> folded into "Payments & Transfers"
- DEPOSIT (ELECTRONIC DEPOSIT) -> folded into "Income"

All other legacy categories (including ATM, which is not payment/deposit-like)
are preserved as their own categories, in original dict order.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import (  # noqa: F401
    Account,
    Bucket,
    Category,
    CategoryKeyword,
    Institution,
    SeedSuppression,
    Workspace,
)
from app.models.seed_suppression import CATEGORY, KEYWORD

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")

#: The one workspace this file's category list belongs to — the
#: pre-workspace data set, adopted by the `g1h2i3j4k5l6` migration.
#: Created on first run if missing (fresh database, nothing to adopt).
INIT_SLUG = "init"
INIT_NAME = "init"


# --- Institutions -----------------------------------------------------------

INSTITUTIONS: list[tuple[str, str]] = [
    ("amex", "Amex"),
    ("capital_one", "Capital One"),
    ("discover", "Discover"),
    ("citi", "Citi"),
    ("schwab", "Schwab"),
    ("wells_fargo", "Wells Fargo"),
]


# --- Categories --------------------------------------------------------------
# Verbatim from the legacy CATEGORY_KEYWORDS dict, preserving key order.
# PAYMENT and DEPOSIT are extracted below and folded into system categories.

_LEGACY_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "GAS": ["GAS", "CHEVRON", "SHELL"],
    "LOANS": ["DEPT EDUCATION STUDENT LN", "TOYOTA ACH RTL"],
    "RENT": ["APPFOLIO", "MAGNIFY REAL EST"],
    "TRAVEL": [
        "AMERICAN AI", "TRIP", "HOTEL", "TOLLS", "DOUBLETREE", "AIRLINE",
        "RENTAL CAR", "EXPEDIA", "HERTZ", "ALAMO", "AVIS", "RENT A CAR",
        "LYFT", "COT*FLT", "SOUTHWES", "SOUTHWEST",
    ],
    "PAYPAL": ["PAYPAL"],
    "AMAZON": ["AMAZON"],
    "GROCERIES": ["TRADER JOE", "WHOLEF", "SPROUTS"],
    "TARGET": ["TARGET"],
    "FOOD": [
        "SALAD", "LA VICTORIA SANTA", "CHINESE FOOD", "CHICKEN", "DOMINO'S",
        "FRUIT", "BERRIES", "CREPE", "GREAT WHITE MELROSE", "YARD HOUSE",
        "PALETERIA", "JACK IN THE BOX", "COFFEE", "SAFEWAY", "IL FORNAIO",
        "KEBAB", "BBQ", "CHIPOTLE", "STARBUCKS", "EATALY", "CAFE", "TEA",
        "DUNKIN", "DISH", "HOUSE OF BAGELS", "THE MELT", "DOORDASH",
        "MENDOCINO", "PRUNEYARD CINEMAS", "PANDA EXPRESS", "PIZZA", "TACOS",
        "BURGER", "RESTAURANT", "NOLA",
    ],
    "AUTO": ["GEICO", "TOYOTA"],
    "COSTCO": ["COSTCO"],
    "STREAMING": ["NETFLIX", "PARAMOUNT+", "DISNEYPLUS", "PEACOCKTV"],
    "PHARMACY": ["PHARMACY", "CVS", "WALGREENS"],
    "GYM": ["MOVEMENT"],
    "ACTIVITIES": [
        "BOWLING", "ESCAPE ROOM", "MUSEUM", "YOGA", "GOLF", "SKATE", "ZOO",
        "AQUARIUM", "KAYAK", "SNOW.COM/VAIL", "SKI", "MLB*SF GIANTS", "GIANTS",
    ],
    "INTERNET": ["INTERNET", "XFINITY", "SONIC.NET"],
    "LAUNDRY": ["KIOSOFT"],
    "APPLE PAY": ["APLPAY"],
    "PARKING": ["PARKING", "PARKING GARAGE", "SMART METERS"],
    "PAYMENT": ["PYMT", "PAYMENT", "PMT"],  # folded -> Payments & Transfers
    "DEPOSIT": ["ELECTRONIC DEPOSIT"],  # folded -> Income
    "ATM": ["ATM WITHDRAWAL"],
    "UTILITIES": ["PGANDE"],
    "SHOPPING": [
        "ANTHROPOLOGIE", "BATH AND BODY WORKS", "LULULEMON",
        "MICHAELS STORES", "SEPHORA", "CRAP EYEWEAR",
    ],
}

_FOLDED_INTO_TRANSFERS = {"PAYMENT"}
_FOLDED_INTO_INCOME = {"DEPOSIT"}

TRANSFER_KEYWORDS = [
    "AUTOPAY", "EPAYMENT", "ONLINE PAYMENT", "THANK YOU", "PYMT", "PMT",
    "CCPYMT", "CARD ONLINE PAYMENT",
]
INCOME_KEYWORDS = ["PAYROLL", "ELECTRONIC DEPOSIT", "DIRECT DEP"]

# Coarse grouping for the Records category dropdown, expressed as bucket
# names (always uppercase — bucket names are stored ALL CAPS). Keyed by
# each category's FINAL seeded name — legacy keys that stayed
# all-uppercase (see the name.title() rule below) must be matched in that
# same case. Anything not listed here (including future user-created
# categories) falls back to the OTHER bucket.
CATEGORY_GROUPS: dict[str, str] = {
    "GAS": "ESSENTIALS",
    "LOANS": "ESSENTIALS",
    "RENT": "ESSENTIALS",
    "UTILITIES": "ESSENTIALS",
    "PHARMACY": "ESSENTIALS",
    "AUTO": "ESSENTIALS",
    "INTERNET": "ESSENTIALS",
    "PARKING": "ESSENTIALS",
    "GROCERIES": "ESSENTIALS",
    "TRAVEL": "LIFESTYLE",
    "PAYPAL": "LIFESTYLE",
    "AMAZON": "LIFESTYLE",
    "TARGET": "LIFESTYLE",
    "FOOD": "LIFESTYLE",
    "COSTCO": "LIFESTYLE",
    "STREAMING": "LIFESTYLE",
    "GYM": "LIFESTYLE",
    "ACTIVITIES": "LIFESTYLE",
    "LAUNDRY": "LIFESTYLE",
    "APPLE PAY": "LIFESTYLE",
    "SHOPPING": "LIFESTYLE",
    "ATM": "OTHER",
    "Uncategorized": "OTHER",
    "Income": "INCOME",
    "Savings": "SAVINGS",
    "Payments & Transfers": "TRANSFERS",
}

# The fixed set of buckets seeded at startup. OTHER is always included
# (and is the undeletable fallback) even though every CATEGORY_GROUPS
# value above also happens to resolve to one of these.
BUCKET_NAMES: list[str] = [
    "ESSENTIALS",
    "LIFESTYLE",
    "INCOME",
    "TRANSFERS",
    "SAVINGS",
    "OTHER",
]


def _build_category_plan() -> list[dict]:
    """Build the ordered list of (name, keywords, flags) to seed.

    Ordering/priority rules:
    - Regular legacy categories keep their original dict order -> ascending
      priority starting at 0.
    - "Payments & Transfers" and "Income" are system/excluded categories;
      they are inserted at the point their legacy counterpart (PAYMENT /
      DEPOSIT) appeared, carrying the union of legacy + plan-specified
      keywords (legacy PAYMENT keywords folded into transfers, legacy
      DEPOSIT keywords folded into income).
    - "Uncategorized" is appended last, at max priority, with no keywords.
    """
    plan: list[dict] = []

    for name, keywords in _LEGACY_CATEGORY_KEYWORDS.items():
        if name in _FOLDED_INTO_TRANSFERS:
            merged = list(dict.fromkeys(TRANSFER_KEYWORDS + keywords))
            plan.append(
                {
                    "name": "Payments & Transfers",
                    "keywords": merged,
                    "is_system": True,
                    "excluded_from_analytics": True,
                }
            )
        elif name in _FOLDED_INTO_INCOME:
            merged = list(dict.fromkeys(INCOME_KEYWORDS + keywords))
            plan.append(
                {
                    "name": "Income",
                    "keywords": merged,
                    "is_system": False,
                    "excluded_from_analytics": True,
                }
            )
        else:
            plan.append(
                {
                    "name": name.title() if not name.isupper() else name,
                    "keywords": keywords,
                    "is_system": False,
                    "excluded_from_analytics": False,
                }
            )

    plan.append(
        {
            "name": "Savings",
            "keywords": [],
            "is_system": False,
            "excluded_from_analytics": False,
        }
    )

    plan.append(
        {
            "name": "Uncategorized",
            "keywords": [],
            "is_system": True,
            "excluded_from_analytics": False,
        }
    )

    for entry in plan:
        entry["group"] = CATEGORY_GROUPS.get(entry["name"], "OTHER")

    return plan


def seed_institutions(db: Session) -> None:
    existing = {code for (code,) in db.query(Institution.code).all()}
    for code, display_name in INSTITUTIONS:
        if code in existing:
            continue
        db.add(Institution(code=code, display_name=display_name))
        logger.info("institution: created %s", code)
    db.flush()


def get_or_create_init_workspace(db: Session) -> Workspace:
    """Return the `init` workspace, creating it if absent.

    Normally the workspaces migration has already created it and
    backfilled every pre-workspace row into it. The create path here is
    for a database built from scratch (fresh dev volume, test setup),
    where the migration had no rows to adopt.
    """
    workspace = db.scalar(select(Workspace).where(Workspace.slug == INIT_SLUG))
    if workspace is None:
        workspace = Workspace(slug=INIT_SLUG, name=INIT_NAME)
        db.add(workspace)
        db.flush()
        logger.info("workspace: created %r", INIT_SLUG)
    return workspace


def seed_buckets(db: Session, workspace: Workspace) -> dict[str, Bucket]:
    """Create the fixed uppercase bucket rows if missing. Idempotent
    lookup-by-name within the workspace; returns a name -> Bucket map for
    the category seed step below."""
    existing = {
        b.name: b
        for b in db.scalars(
            select(Bucket).where(Bucket.workspace_id == workspace.id)
        ).all()
    }
    for name in BUCKET_NAMES:
        if name in existing:
            continue
        bucket = Bucket(workspace_id=workspace.id, name=name)
        db.add(bucket)
        db.flush()
        existing[name] = bucket
        logger.info("bucket: created %r", name)
    return existing


def seed_categories_and_keywords(
    db: Session, workspace: Workspace, buckets_by_name: dict[str, Bucket]
) -> None:
    plan = _build_category_plan()

    # Keyword uniqueness is per-workspace, and the plan is walked in
    # priority order (lower index = higher precedence, i.e. seen first wins).
    claimed_keywords: dict[str, str] = {}  # keyword -> category name that owns it

    existing_categories = {
        c.name: c
        for c in db.scalars(
            select(Category).where(Category.workspace_id == workspace.id)
        ).all()
    }
    existing_keywords = {
        k.keyword
        for k in db.scalars(
            select(CategoryKeyword).where(
                CategoryKeyword.workspace_id == workspace.id
            )
        ).all()
    }

    # Items the user deleted through the UI. This seeder is get-or-create by
    # name and runs on every backend start, so without these tombstones an
    # absent row looks identical to a never-seeded one and gets recreated —
    # silently undoing the deletion on the next restart.
    suppressed = {
        (s.kind, s.name)
        for s in db.scalars(
            select(SeedSuppression).where(
                SeedSuppression.workspace_id == workspace.id
            )
        ).all()
    }

    next_priority = 0
    for entry in plan:
        name = entry["name"]
        bucket = buckets_by_name[entry["group"]]
        category = existing_categories.get(name)

        if category is None and (CATEGORY, name) in suppressed:
            logger.info("category: skipped %r (deleted by user)", name)
            next_priority += 1
            continue

        if category is None:
            category = Category(
                workspace_id=workspace.id,
                name=name,
                is_system=entry["is_system"],
                excluded_from_analytics=entry["excluded_from_analytics"],
                priority=next_priority,
                bucket_id=bucket.id,
            )
            db.add(category)
            db.flush()
            existing_categories[name] = category
            logger.info("category: created %r (priority=%d)", name, next_priority)
        # An existing category's bucket is left alone: this used to re-sync
        # to the plan's value on every run, which reverted any bucket move
        # the user made through the UI the next time the backend restarted.
        next_priority += 1

        for raw_kw in entry["keywords"]:
            kw = raw_kw.upper().strip()
            if not kw:
                continue

            owner = claimed_keywords.get(kw)
            if owner is not None and owner != name:
                logger.info(
                    "keyword %r: skipped for %r (already claimed by higher-"
                    "priority category %r)",
                    kw, name, owner,
                )
                continue
            claimed_keywords[kw] = name

            if kw in existing_keywords:
                continue  # already persisted from a prior run

            if (KEYWORD, kw) in suppressed:
                logger.info("keyword: skipped %r -> %r (removed by user)", kw, name)
                continue

            db.add(
                CategoryKeyword(
                    workspace_id=workspace.id,
                    category_id=category.id,
                    keyword=kw,
                )
            )
            existing_keywords.add(kw)
            logger.info("keyword: created %r -> %r", kw, name)

    db.flush()


def run() -> None:
    # Ensure tables exist even if called standalone (normally Alembic owns
    # this, but it keeps the script safe to invoke directly in dev/tests).
    Base.metadata.create_all(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        seed_institutions(db)
        workspace = get_or_create_init_workspace(db)
        buckets_by_name = seed_buckets(db, workspace)
        seed_categories_and_keywords(db, workspace, buckets_by_name)
        db.commit()
        logger.info("seed: complete")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
