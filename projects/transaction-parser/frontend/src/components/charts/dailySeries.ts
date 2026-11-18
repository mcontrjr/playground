import type { DailyPoint } from '../../api/types'
import { assignSeriesColors, OTHER_LABEL } from './palette'
import type { LegendEntry } from './ChartLegend'
import { formatMonthPeriod } from './format'

const DAY_FORMATTER = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })
export const RUNNING_TOTAL_COLOR = 'var(--ink)'

/** Point granularity the shared series-building pipeline can be fed:
 * `'day'` for per-month drill-down (`point.date` is a full ISO day,
 * e.g. "2026-09-14") or `'month'` for the "All records" view
 * (`point.date` is a "YYYY-MM" period, e.g. "2026-09"). Everything
 * that depends on how a "point" steps forward — the gap-filling
 * cursor, the row key format, and the axis label — branches on this. */
export type PointGranularity = 'day' | 'month'

export function formatDay(iso: string): string {
  return DAY_FORMATTER.format(new Date(`${iso}T00:00:00`))
}

/** Label for a row's key, given the granularity it was built with. */
function formatPointLabel(key: string, granularity: PointGranularity): string {
  return granularity === 'month' ? formatMonthPeriod(key) : formatDay(key)
}

export interface SeriesRow {
  key: string
  label: string
  running: number | null
  /** True only for rows backed by an actual API point (a day/month that
   * had at least one transaction) — gates which rows get a visible,
   * clickable running-total dot so a blank day never renders one. */
  hasTransaction: boolean
  [categoryKey: string]: string | number | boolean | null
}

/**
 * Picks the set of categories to give their own stacked-bar color,
 * ranked by total spend across the WHOLE period (not per-point) so a
 * category's color and stacking position stay the same from one
 * point's bar to the next — a category that's small on one day/month
 * and huge on another would otherwise jump between "its own slot" and
 * "Other" day to day, which defeats the point of a stable legend.
 */
export function rankCategories(points: DailyPoint[]): { key: string; name: string }[] {
  const totals = new Map<string, { name: string; total: number }>()
  for (const point of points) {
    for (const entry of point.by_category) {
      const key = entry.category_id != null ? String(entry.category_id) : entry.name
      const existing = totals.get(key)
      if (existing) {
        existing.total += Number(entry.amount)
      } else {
        totals.set(key, { name: entry.name, total: Number(entry.amount) })
      }
    }
  }
  return [...totals.entries()]
    .sort((a, b) => b[1].total - a[1].total)
    .map(([key, v]) => ({ key, name: v.name }))
}

function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Expands the API's sparse per-day points (one row per day THAT HAD a
 * transaction) into one row per CALENDAR day in the span, so the bar
 * chart's category axis has a blank slot for every skipped day. A bar
 * chart's categories are evenly spaced regardless of what they
 * represent, so without this step, a run with no activity would look
 * identical to one with daily activity — inserting the blank days is
 * what actually renders as a visible gap. The running-total line
 * carries its value forward through blank days (it's cumulative, so
 * it shouldn't dip to nothing just because a day had no transaction);
 * the stacked bars do not.
 *
 * This day-stepping/gap-filling only applies for `granularity: 'day'`
 * (per-month drill-down, where `point.date` is a full ISO day). For
 * `granularity: 'month'` ("All records", where `point.date` is a
 * "YYYY-MM" period) there's nothing to fill: the API already returns
 * one row per period with no gaps, so each point maps straight to a
 * row in order, keyed and labeled as a month rather than a day.
 */
export function buildDailyRows(
  points: DailyPoint[],
  categoryOrder: { key: string; name: string }[],
  granularity: PointGranularity = 'day',
  /** Day granularity only: the calendar month's first/last day
   * ("YYYY-MM-DD"). When given, the row span runs the FULL month
   * (1st through last day) regardless of which days have
   * transactions, so the running total visibly starts at 0 on the
   * 1st — not at whatever day the first transaction happened to fall
   * on. Falls back to spanning just the points themselves if omitted
   * (e.g. the "All" monthly-period view never needs this). */
  monthBounds?: { from: string; to: string },
): SeriesRow[] {
  if (granularity === 'month') {
    return points.map((point) => {
      const row: SeriesRow = {
        key: point.date,
        label: formatPointLabel(point.date, granularity),
        running: Number(point.running_total),
        hasTransaction: true,
      }
      for (const c of categoryOrder) row[c.key] = null
      for (const entry of point.by_category) {
        const key = entry.category_id != null ? String(entry.category_id) : entry.name
        row[key] = Number(entry.amount)
      }
      return row
    })
  }

  if (points.length === 0 && !monthBounds) return []

  const rows: SeriesRow[] = []
  const startIso = monthBounds?.from ?? points[0]!.date
  const endIso = monthBounds?.to ?? points[points.length - 1]!.date
  let cursor = new Date(`${startIso}T00:00:00`)
  const last = new Date(`${endIso}T00:00:00`)
  const byDate = new Map(points.map((p) => [p.date, p]))
  let lastRunning = 0

  while (cursor <= last) {
    const iso = toIsoDate(cursor)
    const point = byDate.get(iso)
    const row: SeriesRow = {
      key: iso,
      label: formatDay(iso),
      running: lastRunning,
      hasTransaction: !!point,
    }
    for (const c of categoryOrder) row[c.key] = null

    if (point) {
      lastRunning = Number(point.running_total)
      row.running = lastRunning
      for (const entry of point.by_category) {
        const key = entry.category_id != null ? String(entry.category_id) : entry.name
        row[key] = Number(entry.amount)
      }
    }
    rows.push(row)
    cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 1)
  }
  return rows
}

export interface RankedSeries {
  rows: SeriesRow[]
  stackKeys: string[]
  colors: string[]
  legendEntries: LegendEntry[]
}

/** Shared top-8 + `__other__` capping, color assignment, and legend
 * building — used by both CategoryBarsChart (daily points) and the
 * "All" monthly view (Time Series page's own monthly rows), so the
 * two never drift out of sync on how overflow categories are folded
 * together. */
export function buildRankedSeries(points: DailyPoint[], granularity: PointGranularity = 'day'): RankedSeries {
  const ranked = rankCategories(points)
  const kept = ranked.slice(0, 8)
  const overflow = ranked.slice(8)
  const stackKeys = overflow.length > 0 ? [...kept.map((c) => c.key), '__other__'] : kept.map((c) => c.key)
  const colors = assignSeriesColors(stackKeys.length)

  const rows = buildDailyRows(points, kept, granularity)
  if (overflow.length > 0) {
    const overflowKeys = new Set(overflow.map((c) => c.key))
    for (const point of points) {
      const row = rows.find((r) => r.key === point.date)
      if (!row) continue
      let otherTotal = 0
      for (const entry of point.by_category) {
        const key = entry.category_id != null ? String(entry.category_id) : entry.name
        if (overflowKeys.has(key)) otherTotal += Number(entry.amount)
      }
      if (otherTotal > 0) row.__other__ = otherTotal
    }
  }

  const legendEntries: LegendEntry[] = kept.map((c, i) => ({ key: c.key, label: c.name, color: colors[i]! }))
  if (overflow.length > 0) {
    legendEntries.push({ key: '__other__', label: OTHER_LABEL, color: colors[colors.length - 1]! })
  }

  return { rows, stackKeys, colors, legendEntries }
}
