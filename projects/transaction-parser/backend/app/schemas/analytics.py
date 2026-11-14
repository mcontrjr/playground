"""Pydantic v2 schemas for the analytics API."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Granularity = Literal["month", "week", "day"]


class AnalyticsSummary(BaseModel):
    """High-level KPI summary over the filtered transaction set."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_spent": "12345.67",
                    "total_in": "15000.00",
                    "net": "2654.33",
                    "transaction_count": 420,
                    "date_from": "2026-01-01",
                    "date_to": "2026-10-31",
                    "avg_monthly_spend": "1234.57",
                }
            ]
        }
    )

    total_spent: Decimal = Field(description="Sum of outflows (negative amounts), as a positive number.")
    total_in: Decimal = Field(description="Sum of inflows (positive amounts).")
    net: Decimal = Field(description="total_in - total_spent.")
    transaction_count: int
    date_from: date | None = Field(description="Earliest txn_date in the filtered set, if any.")
    date_to: date | None = Field(description="Latest txn_date in the filtered set, if any.")
    avg_monthly_spend: Decimal = Field(
        description="total_spent divided by the number of calendar months spanned (min 1)."
    )
    largest_transaction: Decimal | None = Field(
        default=None,
        description="Largest single outflow (absolute value) in the filtered set, as a positive number. Null if there are none.",
    )


class TimeseriesSeriesPoint(BaseModel):
    """One category's signed sum for a single period, aligned by index
    with the response's `periods` list."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"period": "2026-09", "value": "-432.10"}]})

    period: str
    value: Decimal


class TimeseriesSeries(BaseModel):
    """One category's full series across all periods, suitable for a
    stacked-bar chart layer."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category_id": 8,
                    "name": "Food",
                    "values": [{"period": "2026-09", "value": "-432.10"}, {"period": "2026-10", "value": "-201.55"}],
                }
            ]
        }
    )

    category_id: int | None
    name: str
    values: list[TimeseriesSeriesPoint]


class TimeseriesResponse(BaseModel):
    """Per-period, per-category signed sums."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "granularity": "month",
                    "periods": ["2026-09", "2026-10"],
                    "series": [
                        {
                            "category_id": 8,
                            "name": "Food",
                            "values": [{"period": "2026-09", "value": "-432.10"}, {"period": "2026-10", "value": "-201.55"}],
                        }
                    ],
                }
            ]
        }
    )

    granularity: Granularity
    periods: list[str] = Field(description="Ordered period labels, e.g. '2026-09' for month, '2026-W37' for week.")
    series: list[TimeseriesSeries]


class DailyCategoryAmount(BaseModel):
    """One category's absolute spend on one day, for the daily bar's
    stacked breakdown."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"category_id": 8, "name": "Food", "amount": "32.10"}]}
    )

    category_id: int | None
    name: str
    amount: Decimal = Field(description="Absolute sum of outflows in this category on this day.")


class DailyPoint(BaseModel):
    """One day's net signed total plus the running accumulated total for
    the month it belongs to — both computed server-side in SQL so the
    Time Series page never recomputes a cumulative sum client-side.
    `by_category` breaks the day's OUTFLOWS down by category (income
    rows aren't part of a spend breakdown), for a stacked bar."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "date": "2026-10-04",
                    "value": "-45.20",
                    "running_total": "-612.40",
                    "by_category": [{"category_id": 8, "name": "Food", "amount": "45.20"}],
                }
            ]
        }
    )

    date: date
    value: Decimal = Field(description="Net signed sum of transactions on this day.")
    running_total: Decimal = Field(
        description="Signed cumulative total from the 1st of this day's month through this day."
    )
    by_category: list[DailyCategoryAmount] = Field(
        description="This day's outflows broken down by category, largest first."
    )


class MonthlyDailySeries(BaseModel):
    """One calendar month's daily series, for the Time Series page's
    single-month swipeable view. `points` only contains days that had at
    least one transaction — the frontend renders gaps between them to
    show elapsed time without a transaction, per the relative x-axis."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "month": "2026-10",
                    "label": "October 2026",
                    "points": [{"date": "2026-10-04", "value": "-45.20", "running_total": "-45.20"}],
                    "month_total": "-1245.30",
                }
            ]
        }
    )

    month: str = Field(description="YYYY-MM")
    label: str = Field(description="Human label, e.g. 'October 2026'.")
    points: list[DailyPoint]
    month_total: Decimal = Field(description="Net signed total for the whole month.")


class DistributionEntry(BaseModel):
    """One category's absolute spend total, for a pie/donut chart."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"category_id": 8, "name": "Food", "amount": "2345.67"}]}
    )

    category_id: int | None
    name: str
    amount: Decimal = Field(description="Absolute sum of outflows for this category.")


class DistributionResponse(BaseModel):
    """Spend-by-category breakdown for a pie chart."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entries": [
                        {"category_id": 8, "name": "Food", "amount": "2345.67"},
                        {"category_id": 11, "name": "Groceries", "amount": "890.12"},
                    ],
                    "total": "3235.79",
                }
            ]
        }
    )

    entries: list[DistributionEntry]
    total: Decimal
