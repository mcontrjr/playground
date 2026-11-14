"""Analytics aggregation service.

All three endpoints (summary, timeseries, distribution) share a common
filtered base query and compute their aggregates in SQL (``SUM``,
``date_trunc``/``to_char`` for period bucketing, ``GROUP BY``) rather
than loading rows into Python, per the plan's performance note.

The exclusion semantics are shared with the transactions API: by
default (``include_excluded=False``) rows whose category has
``excluded_from_analytics=True`` (currently "Payments & Transfers" and
"Income") are left out of every aggregate; passing
``include_excluded=True`` includes them.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models import Category, Transaction
from app.services.cache import cached


@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    date_from: date | None = None
    date_to: date | None = None
    account_ids: tuple[int, ...] | None = None
    include_excluded: bool = False


def _apply_filters(stmt: Select, filters: AnalyticsFilters) -> Select:
    if filters.date_from is not None:
        stmt = stmt.where(Transaction.txn_date >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(Transaction.txn_date <= filters.date_to)
    if filters.account_ids:
        stmt = stmt.where(Transaction.account_id.in_(filters.account_ids))
    if not filters.include_excluded:
        stmt = stmt.where(
            func.coalesce(Category.excluded_from_analytics, False).is_(False)
        )
    return stmt


@dataclass(frozen=True, slots=True)
class SummaryResult:
    total_spent: Decimal
    total_in: Decimal
    net: Decimal
    transaction_count: int
    date_from: date | None
    date_to: date | None
    avg_monthly_spend: Decimal
    largest_transaction: Decimal | None


@cached
def compute_summary(db: Session, filters: AnalyticsFilters) -> SummaryResult:
    base = (
        select(Transaction.amount, Transaction.txn_date)
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
    )
    base = _apply_filters(base, filters)
    sub = base.subquery()

    agg_stmt = select(
        func.coalesce(
            func.sum(case((sub.c.amount < 0, -sub.c.amount), else_=0)), 0
        ).label("total_spent"),
        func.coalesce(
            func.sum(case((sub.c.amount > 0, sub.c.amount), else_=0)), 0
        ).label("total_in"),
        func.coalesce(func.sum(sub.c.amount), 0).label("net"),
        func.count().label("txn_count"),
        func.min(sub.c.txn_date).label("min_date"),
        func.max(sub.c.txn_date).label("max_date"),
        func.max(case((sub.c.amount < 0, -sub.c.amount), else_=0)).label("largest_txn"),
    )
    row = db.execute(agg_stmt).one()

    total_spent = Decimal(row.total_spent)
    total_in = Decimal(row.total_in)
    net = Decimal(row.net)
    min_date = row.min_date
    max_date = row.max_date
    largest_transaction = (
        Decimal(row.largest_txn).quantize(Decimal("0.01"))
        if row.largest_txn is not None and row.txn_count > 0
        else None
    )

    if min_date is not None and max_date is not None:
        months_spanned = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
        months_spanned = max(months_spanned, 1)
    else:
        months_spanned = 1

    avg_monthly_spend = (total_spent / Decimal(months_spanned)).quantize(Decimal("0.01"))

    return SummaryResult(
        total_spent=total_spent.quantize(Decimal("0.01")),
        total_in=total_in.quantize(Decimal("0.01")),
        net=net.quantize(Decimal("0.01")),
        transaction_count=row.txn_count,
        date_from=min_date,
        date_to=max_date,
        avg_monthly_spend=avg_monthly_spend,
        largest_transaction=largest_transaction,
    )


@dataclass(frozen=True, slots=True)
class TimeseriesRow:
    period: str
    category_id: int | None
    category_name: str
    value: Decimal


@cached
def compute_timeseries(
    db: Session, filters: AnalyticsFilters, granularity: str
) -> list[TimeseriesRow]:
    """Per-period, per-category signed sums.

    ``granularity`` is "month" (``YYYY-MM``) or "week" (``YYYY-"W"WW``,
    ISO week), computed in SQL via ``to_char(date_trunc(...))``.
    """
    if granularity == "month":
        period_expr = func.to_char(func.date_trunc("month", Transaction.txn_date), "YYYY-MM")
    else:
        period_expr = func.concat(
            func.to_char(Transaction.txn_date, "IYYY"),
            "-W",
            func.to_char(Transaction.txn_date, "IW"),
        )

    category_name_expr = func.coalesce(Category.name, "Uncategorized")

    stmt = (
        select(
            period_expr.label("period"),
            Transaction.category_id.label("category_id"),
            category_name_expr.label("category_name"),
            func.sum(Transaction.amount).label("value"),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
    )
    stmt = _apply_filters(stmt, filters)
    stmt = stmt.group_by("period", Transaction.category_id, category_name_expr).order_by("period")

    rows = db.execute(stmt).all()
    return [
        TimeseriesRow(
            period=r.period,
            category_id=r.category_id,
            category_name=r.category_name,
            value=Decimal(r.value).quantize(Decimal("0.01")),
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class DistributionRow:
    category_id: int | None
    category_name: str
    amount: Decimal


@cached
def compute_distribution(db: Session, filters: AnalyticsFilters) -> list[DistributionRow]:
    """Absolute sum of outflows (amount < 0) per category, for a pie chart."""
    category_name_expr = func.coalesce(Category.name, "Uncategorized")

    stmt = (
        select(
            Transaction.category_id.label("category_id"),
            category_name_expr.label("category_name"),
            func.sum(-Transaction.amount).label("amount"),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(Transaction.amount < 0)
    )
    stmt = _apply_filters(stmt, filters)
    stmt = stmt.group_by(Transaction.category_id, category_name_expr).order_by(
        func.sum(-Transaction.amount).desc()
    )

    rows = db.execute(stmt).all()
    return [
        DistributionRow(
            category_id=r.category_id,
            category_name=r.category_name,
            amount=Decimal(r.amount).quantize(Decimal("0.01")),
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class DailyCategoryAmount:
    category_id: int | None
    category_name: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class DailyPointRow:
    day: date
    value: Decimal
    running_total: Decimal
    by_category: list[DailyCategoryAmount]


@dataclass(frozen=True, slots=True)
class MonthlyDailySeriesResult:
    month: str
    label: str
    points: list[DailyPointRow]
    month_total: Decimal


@cached
def compute_monthly_daily_series(
    db: Session,
    month: date,
    account_ids: tuple[int, ...] | None,
    include_excluded: bool,
) -> MonthlyDailySeriesResult:
    """One calendar month's per-day net totals plus a running cumulative
    total, computed entirely in SQL via a window function — the Time
    Series page's "swipe one month at a time, right axis shows the
    month's running total" view needs exactly this shape and nothing
    the frontend has to re-derive.

    Only days with at least one transaction appear in ``points``; the
    frontend is responsible for rendering the gap between non-adjacent
    days (the "relative x-axis" requirement) rather than the backend
    padding in zero-days, which would defeat the point of showing gaps.
    """
    year, month_num = month.year, month.month
    month_start = date(year, month_num, 1)
    days_in_month = calendar.monthrange(year, month_num)[1]
    month_end = date(year, month_num, days_in_month)

    filters = AnalyticsFilters(
        date_from=month_start,
        date_to=month_end,
        account_ids=account_ids,
        include_excluded=include_excluded,
    )

    base = (
        select(
            Transaction.amount,
            Transaction.txn_date,
            Transaction.category_id,
            func.coalesce(Category.name, "Uncategorized").label("category_name"),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
    )
    base = _apply_filters(base, filters)
    daily = base.subquery()

    per_day = (
        select(
            daily.c.txn_date.label("day"),
            func.sum(daily.c.amount).label("value"),
        )
        .group_by(daily.c.txn_date)
        .subquery()
    )

    running_stmt = select(
        per_day.c.day,
        per_day.c.value,
        func.sum(per_day.c.value)
        .over(order_by=per_day.c.day)
        .label("running_total"),
    ).order_by(per_day.c.day)

    rows = db.execute(running_stmt).all()

    # Per-day, per-category spend breakdown (absolute outflows only —
    # same convention as /analytics/distribution — so the stacked bars
    # decompose "how much you spent that day" by category; income rows
    # don't participate in a spend breakdown).
    category_stmt = (
        select(
            daily.c.txn_date.label("day"),
            daily.c.category_id.label("category_id"),
            daily.c.category_name.label("category_name"),
            func.sum(-daily.c.amount).label("amount"),
        )
        .where(daily.c.amount < 0)
        .group_by(daily.c.txn_date, daily.c.category_id, daily.c.category_name)
        .order_by(daily.c.txn_date, func.sum(-daily.c.amount).desc())
    )
    category_rows = db.execute(category_stmt).all()
    by_day: dict[date, list[DailyCategoryAmount]] = {}
    for r in category_rows:
        by_day.setdefault(r.day, []).append(
            DailyCategoryAmount(
                category_id=r.category_id,
                category_name=r.category_name,
                amount=Decimal(r.amount).quantize(Decimal("0.01")),
            )
        )

    points = [
        DailyPointRow(
            day=r.day,
            value=Decimal(r.value).quantize(Decimal("0.01")),
            running_total=Decimal(r.running_total).quantize(Decimal("0.01")),
            by_category=by_day.get(r.day, []),
        )
        for r in rows
    ]
    month_total = points[-1].running_total if points else Decimal("0.00")

    return MonthlyDailySeriesResult(
        month=f"{year}-{month_num:02d}",
        label=month_start.strftime("%B %Y"),
        points=points,
        month_total=month_total,
    )
