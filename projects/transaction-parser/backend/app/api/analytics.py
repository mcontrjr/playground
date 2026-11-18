"""Aggregated analytics endpoints: summary KPIs, timeseries, distribution.

All three share the same filter semantics as the transactions API:
"Income" categorized rows are always included, and ``include_excluded``
(default false) drops rows whose category is flagged
``excluded_from_analytics`` (transfers). All aggregation happens in
SQL via ``app.services.analytics_service``.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.analytics import (
    AnalyticsSummary,
    DailyCategoryAmount,
    DailyPoint,
    DistributionEntry,
    DistributionResponse,
    Granularity,
    MonthlyDailySeries,
    TimeseriesResponse,
    TimeseriesSeries,
    TimeseriesSeriesPoint,
)
from app.services.analytics_service import (
    AnalyticsFilters,
    compute_distribution,
    compute_monthly_daily_series,
    compute_summary,
    compute_timeseries,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _filters(
    date_from: date | None,
    date_to: date | None,
    account_ids: list[int] | None,
    include_excluded: bool,
) -> AnalyticsFilters:
    return AnalyticsFilters(
        date_from=date_from,
        date_to=date_to,
        account_ids=tuple(account_ids) if account_ids else None,
        include_excluded=include_excluded,
    )


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Top-line KPIs",
    description=(
        "Total spent (absolute sum of outflows), total in, net, transaction "
        "count, date range, and average monthly spend over the filtered set."
    ),
)
def get_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    account_ids: list[int] | None = Query(None),
    include_excluded: bool = Query(False, description="Include transfer/income categories."),
    db: Session = Depends(get_db),
) -> AnalyticsSummary:
    filters = _filters(date_from, date_to, account_ids, include_excluded)
    result = compute_summary(db, filters)
    return AnalyticsSummary(
        total_spent=result.total_spent,
        total_in=result.total_in,
        net=result.net,
        transaction_count=result.transaction_count,
        date_from=result.date_from,
        date_to=result.date_to,
        avg_monthly_spend=result.avg_monthly_spend,
        largest_transaction=result.largest_transaction,
    )


@router.get(
    "/timeseries",
    response_model=TimeseriesResponse,
    summary="Per-period, per-category signed sums",
    description=(
        "Shaped for a stacked bar chart: an ordered list of period labels "
        "plus one series per category, each carrying one signed sum per "
        "period (0 where the category had no activity that period)."
    ),
)
def get_timeseries(
    granularity: Granularity = Query("month"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    account_ids: list[int] | None = Query(None),
    include_excluded: bool = Query(False, description="Include transfer/income categories."),
    db: Session = Depends(get_db),
) -> TimeseriesResponse:
    filters = _filters(date_from, date_to, account_ids, include_excluded)
    rows = compute_timeseries(db, filters, granularity)

    periods: list[str] = sorted({r.period for r in rows})
    period_index = {p: i for i, p in enumerate(periods)}

    series_by_category: dict[int | None, TimeseriesSeries] = {}
    for row in rows:
        series = series_by_category.get(row.category_id)
        if series is None:
            series = TimeseriesSeries(category_id=row.category_id, name=row.category_name, values=[])
            series_by_category[row.category_id] = series
        series.values.append(TimeseriesSeriesPoint(period=row.period, value=row.value))

    # Fill gaps so every series has one point per period, in period order.
    filled_series: list[TimeseriesSeries] = []
    for series in series_by_category.values():
        by_period = {v.period: v.value for v in series.values}
        values = [
            TimeseriesSeriesPoint(period=p, value=by_period.get(p, 0))
            for p in periods
        ]
        filled_series.append(TimeseriesSeries(category_id=series.category_id, name=series.name, values=values))

    filled_series.sort(key=lambda s: s.name)

    return TimeseriesResponse(granularity=granularity, periods=periods, series=filled_series)


@router.get(
    "/monthly-daily",
    response_model=MonthlyDailySeries,
    summary="One month's per-day net totals with a running cumulative total",
    description=(
        "The Time Series page's primary view: every day in `month` that had "
        "at least one transaction, its net signed total, and the running "
        "total accumulated since the 1st of that month — all computed in SQL. "
        "Days with no activity are omitted (not zero-filled) so the frontend "
        "can render the actual gap in time between transactions."
    ),
)
def get_monthly_daily(
    month: date = Query(..., description="Any date within the target month; only year/month are used."),
    account_ids: list[int] | None = Query(None),
    include_excluded: bool = Query(False, description="Include transfer/income categories."),
    db: Session = Depends(get_db),
) -> MonthlyDailySeries:
    result = compute_monthly_daily_series(
        db,
        date(month.year, month.month, 1),
        tuple(account_ids) if account_ids else None,
        include_excluded,
    )
    return MonthlyDailySeries(
        month=result.month,
        label=result.label,
        points=[
            DailyPoint(
                date=p.day,
                value=p.value,
                running_total=p.running_total,
                by_category=[
                    DailyCategoryAmount(category_id=c.category_id, name=c.category_name, amount=c.amount)
                    for c in p.by_category
                ],
            )
            for p in result.points
        ],
        month_total=result.month_total,
    )


@router.get(
    "/distribution",
    response_model=DistributionResponse,
    summary="Spend by category",
    description="Absolute sum of outflows per category, for a pie/donut chart, sorted largest first.",
)
def get_distribution(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    account_ids: list[int] | None = Query(None),
    include_excluded: bool = Query(False, description="Include transfer/income categories."),
    db: Session = Depends(get_db),
) -> DistributionResponse:
    filters = _filters(date_from, date_to, account_ids, include_excluded)
    rows = compute_distribution(db, filters)
    entries = [
        DistributionEntry(category_id=r.category_id, name=r.category_name, amount=r.amount)
        for r in rows
    ]
    total = sum((e.amount for e in entries), start=Decimal("0"))
    return DistributionResponse(entries=entries, total=total)
