import { useMemo, useState } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DailyPoint } from '../../api/types'
import { ChartLegend, type LegendEntry } from './ChartLegend'
import { ChartTooltip, type ChartTooltipRow } from './ChartTooltip'
import { formatCurrency } from './format'
import { assignSeriesColors, OTHER_LABEL } from './palette'
import styles from './DailySeriesChart.module.css'

interface DailySeriesChartProps {
  points: DailyPoint[]
  height?: number
}

const DAY_FORMATTER = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })
const RUNNING_TOTAL_COLOR = 'var(--ink)'

function formatDay(iso: string): string {
  return DAY_FORMATTER.format(new Date(`${iso}T00:00:00`))
}

interface Row {
  key: string
  label: string
  running: number | null
  [categoryKey: string]: string | number | null
}

/**
 * Picks the set of categories to give their own stacked-bar color,
 * ranked by total spend across the WHOLE MONTH (not per-day) so a
 * category's color and stacking position stay the same from one day's
 * bar to the next — a category that's small on one day and huge on
 * another would otherwise jump between "its own slot" and "Other"
 * day to day, which defeats the point of a stable legend.
 */
function rankCategories(points: DailyPoint[]): { key: string; name: string }[] {
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

/**
 * Expands the API's sparse per-day points (one row per day THAT HAD a
 * transaction) into one row per CALENDAR day in the span, so the bar
 * chart's category axis has a blank slot for every skipped day. A bar
 * chart's categories are evenly spaced regardless of what they
 * represent, so without this step, a run with no activity would look
 * identical to one with daily activity — inserting the blank days is
 * what actually renders as a visible gap, satisfying the "relative
 * x-axis" requirement. The running-total line carries its value
 * forward through blank days (it's cumulative, so it shouldn't dip to
 * nothing just because a day had no transaction); the stacked bars do
 * not.
 */
function buildRows(points: DailyPoint[], categoryOrder: { key: string; name: string }[]): Row[] {
  if (points.length === 0) return []
  const rows: Row[] = []
  let cursor = new Date(`${points[0]!.date}T00:00:00`)
  const last = new Date(`${points[points.length - 1]!.date}T00:00:00`)
  const byDate = new Map(points.map((p) => [p.date, p]))
  let lastRunning = 0

  while (cursor <= last) {
    const iso = toIsoDate(cursor)
    const point = byDate.get(iso)
    const row: Row = { key: iso, label: point ? formatDay(iso) : '', running: lastRunning }
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

function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

type AxisFocus = 'daily' | 'running' | null

export function DailySeriesChart({ points, height = 360 }: DailySeriesChartProps) {
  const [axisFocus, setAxisFocus] = useState<AxisFocus>(null)
  const { rows, stackKeys, colors, legendEntries } = useMemo(() => {
    const ranked = rankCategories(points)
    const kept = ranked.slice(0, 8)
    const overflow = ranked.slice(8)
    const stackKeys = overflow.length > 0 ? [...kept.map((c) => c.key), '__other__'] : kept.map((c) => c.key)
    const colors = assignSeriesColors(stackKeys.length)

    const expandedRows = buildRows(points, kept)
    if (overflow.length > 0) {
      const overflowKeys = new Set(overflow.map((c) => c.key))
      for (const point of points) {
        const row = expandedRows.find((r) => r.key === point.date)
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
    legendEntries.push({ key: 'running', label: 'Running total (right axis)', color: RUNNING_TOTAL_COLOR })

    return { rows: expandedRows, stackKeys, colors, legendEntries }
  }, [points])

  return (
    <div className={styles.wrap}>
      <div className={styles.axisLabels}>
        <span className={styles.axisLabelLeft}>↙ Daily spend by category</span>
        <span className={styles.axisLabelRight}>Running total this month ↘</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={rows} margin={{ top: 8, right: 8, left: 4, bottom: 4 }} barCategoryGap="20%">
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            interval="preserveStartEnd"
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink)' }}
          />
          <YAxis
            yAxisId="daily"
            axisLine={{ stroke: 'var(--series-1)' }}
            tickLine={false}
            width={56}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--series-1)' }}
            tickFormatter={(v: number) => formatCurrency(v)}
            onMouseEnter={() => setAxisFocus('daily')}
            onMouseLeave={() => setAxisFocus(null)}
            style={{ cursor: 'pointer' }}
          />
          <YAxis
            yAxisId="running"
            orientation="right"
            axisLine={{ stroke: RUNNING_TOTAL_COLOR }}
            tickLine={false}
            width={64}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: RUNNING_TOTAL_COLOR }}
            tickFormatter={(v: number) => formatCurrency(v)}
            onMouseEnter={() => setAxisFocus('running')}
            onMouseLeave={() => setAxisFocus(null)}
            style={{ cursor: 'pointer' }}
          />
          <Tooltip
            cursor={{ fill: 'var(--paper-sunk)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const runningPayload = payload.find((p) => p.dataKey === 'running')
              const categoryRows = payload.filter((p) => p.dataKey !== 'running' && typeof p.value === 'number' && p.value > 0)
              if (categoryRows.length === 0 && runningPayload?.value == null) return null
              const tooltipRows: ChartTooltipRow[] = categoryRows
                .map((p) => ({
                  key: String(p.dataKey),
                  label: String(p.name),
                  value: Number(p.value),
                  color: String(p.color),
                }))
                .sort((a, b) => b.value - a.value)
              if (runningPayload?.value != null) {
                tooltipRows.push({
                  key: 'running',
                  label: 'Running total',
                  value: Number(runningPayload.value),
                  color: RUNNING_TOTAL_COLOR,
                })
              }
              return <ChartTooltip heading={String(label)} rows={tooltipRows} />
            }}
          />
          {stackKeys.map((key, i) => (
            <Bar
              key={key}
              yAxisId="daily"
              dataKey={key}
              name={legendEntries.find((e) => e.key === key)?.label ?? key}
              stackId="spend"
              fill={colors[i]}
              stroke="var(--paper)"
              strokeWidth={1}
              maxBarSize={22}
              opacity={axisFocus === 'running' ? 0.25 : 1}
              isAnimationActive={false}
            />
          ))}
          <Line
            yAxisId="running"
            dataKey="running"
            name="Running total"
            stroke={RUNNING_TOTAL_COLOR}
            strokeWidth={axisFocus === 'running' ? 3 : 2}
            strokeOpacity={axisFocus === 'daily' ? 0.25 : 1}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <ChartLegend entries={legendEntries} />
    </div>
  )
}
