"""Idempotent seed script: institutions, categories, and category keywords.

Safe to run on every startup (and does so, via docker-compose's backend
command). Uses INSERT-if-missing / get-or-create patterns throughout so
repeated runs never raise integrity errors and never change existing data
beyond filling in what's missing.

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

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Account, Category, CategoryKeyword, Institution  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")


# --- Institutions -----------------------------------------------------------

INSTITUTIONS: list[tuple[str, str]] = [
    ("amex", "Amex"),
    ("capital_one", "Capital One"),
    ("discover", "Discover"),
    ("citi", "Citi"),
    ("schwab", "Schwab"),
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

# Coarse grouping for the Records category dropdown. Keyed by each
# category's FINAL seeded name — legacy keys that stayed all-uppercase
# (see the name.title() rule below) must be matched in that same case.
# Anything not listed here (including future user-created categories)
# falls back to "Other" client-side.
CATEGORY_GROUPS: dict[str, str] = {
    "GAS": "Essentials",
    "LOANS": "Essentials",
    "RENT": "Essentials",
    "UTILITIES": "Essentials",
    "PHARMACY": "Essentials",
    "AUTO": "Essentials",
    "INTERNET": "Essentials",
    "PARKING": "Essentials",
    "GROCERIES": "Essentials",
    "TRAVEL": "Lifestyle",
    "PAYPAL": "Lifestyle",
    "AMAZON": "Lifestyle",
    "TARGET": "Lifestyle",
    "FOOD": "Lifestyle",
    "COSTCO": "Lifestyle",
    "STREAMING": "Lifestyle",
    "GYM": "Lifestyle",
    "ACTIVITIES": "Lifestyle",
    "LAUNDRY": "Lifestyle",
    "APPLE PAY": "Lifestyle",
    "SHOPPING": "Lifestyle",
    "ATM": "Other",
    "Uncategorized": "Other",
    "Income": "Income",
    "Savings": "Savings",
    "Payments & Transfers": "Transfers",
}


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
        entry["group"] = CATEGORY_GROUPS.get(entry["name"], "Other")

    return plan


def seed_institutions(db: Session) -> None:
    existing = {code for (code,) in db.query(Institution.code).all()}
    for code, display_name in INSTITUTIONS:
        if code in existing:
            continue
        db.add(Institution(code=code, display_name=display_name))
        logger.info("institution: created %s", code)
    db.flush()


def seed_categories_and_keywords(db: Session) -> None:
    plan = _build_category_plan()

    # Globally-unique keyword guard across the whole plan, by priority order
    # (lower priority index = higher precedence, i.e. seen first wins).
    claimed_keywords: dict[str, str] = {}  # keyword -> category name that owns it

    existing_categories = {c.name: c for c in db.query(Category).all()}
    existing_keywords = {k.keyword for k in db.query(CategoryKeyword).all()}

    next_priority = 0
    for entry in plan:
        name = entry["name"]
        category = existing_categories.get(name)
        if category is None:
            category = Category(
                name=name,
                is_system=entry["is_system"],
                excluded_from_analytics=entry["excluded_from_analytics"],
                priority=next_priority,
                group=entry["group"],
            )
            db.add(category)
            db.flush()
            existing_categories[name] = category
            logger.info("category: created %r (priority=%d)", name, next_priority)
        elif category.group != entry["group"]:
            # Re-sync group to the plan's value on every run. This only
            # ever touches the ~20 seeded legacy categories (matched by
            # name); a user's own categories, created via POST /categories,
            # are never in CATEGORY_GROUPS and are untouched by this branch.
            category.group = entry["group"]
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

            db.add(CategoryKeyword(category_id=category.id, keyword=kw))
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
        seed_categories_and_keywords(db)
        db.commit()
        logger.info("seed: complete")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
