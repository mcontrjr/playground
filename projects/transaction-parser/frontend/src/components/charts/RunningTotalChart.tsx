import { useMemo } from 'react'
import { CartesianGrid, Dot, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DotItemDotProps } from 'recharts'
import type { DailyPoint } from '../../api/types'
import type { SeriesRow } from './dailySeries'
import { buildDailyRows, rankCategories, RUNNING_TOTAL_COLOR, type PointGranularity } from './dailySeries'
import { ChartTooltip } from './ChartTooltip'
import { formatCurrency } from './format'
import styles from './RunningTotalChart.module.css'

interface RunningTotalChartProps {
  points: DailyPoint[]
  height?: number
  selectedKey?: string | null
  onPointClick?: (dateKey: string) => void
  /** Whether `points` are per-day rows (per-month drill-down) or
   * per-month "YYYY-MM" rows (All records). Defaults to `'day'` to
   * match this component's original, only use case. */
  granularity?: PointGranularity
  /** Day granularity only: the active month's first/last day, so the
   * line always runs the full 1st-through-last-day span (starting at
   * 0 if the 1st itself has no transaction) instead of starting at
   * whichever day the first transaction happened to land on. */
  monthBounds?: { from: string; to: string }
}

/** The cumulative running-total half of what used to be
 * DailySeriesChart's dual-axis ComposedChart — stacked below
 * CategoryBarsChart so each gets its own, undistorted axis instead of
 * sharing one chart where the running total's scale dwarfs individual
 * days' bars. */
export function RunningTotalChart({
  points,
  height = 220,
  selectedKey,
  onPointClick,
  granularity = 'day',
  monthBounds,
}: RunningTotalChartProps) {
  const rows = useMemo(
    () => buildDailyRows(points, rankCategories(points).slice(0, 8), granularity, monthBounds),
    [points, granularity, monthBounds],
  )

  return (
    <div className={styles.wrap}>
      <span className={styles.axisLabel}>Running total</span>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={rows}
          margin={{ top: 8, right: 8, left: 4, bottom: 4 }}
        >
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            interval="preserveStartEnd"
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink)' }}
          />
          <YAxis
            axisLine={{ stroke: RUNNING_TOTAL_COLOR }}
            tickLine={false}
            width={64}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: RUNNING_TOTAL_COLOR }}
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <Tooltip
            cursor={{ stroke: 'var(--hairline-strong)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const running = payload.find((p) => p.dataKey === 'running')
              if (running?.value == null) return null
              return (
                <ChartTooltip
                  heading={String(label)}
                  rows={[
                    { key: 'running', label: 'Running total', value: Number(running.value), color: RUNNING_TOTAL_COLOR },
                  ]}
                />
              )
            }}
          />
          <Line
            dataKey="running"
            name="Running total"
            stroke={RUNNING_TOTAL_COLOR}
            strokeWidth={2}
            isAnimationActive={false}
            dot={(dotProps: DotItemDotProps) => {
              const payload = dotProps.payload as SeriesRow | undefined
              const isSelected = !!selectedKey && payload?.key === selectedKey
              const hasTransaction = !!payload?.hasTransaction
              const handleClick = () => {
                if (payload && onPointClick) onPointClick(payload.key)
              }
              return (
                <g key={payload?.key ?? dotProps.index}>
                  {/* Visible dot — only drawn (non-zero radius) for the
                   * selected point. Never drawn on a blank day: the line
                   * still runs through it (the running total doesn't
                   * change on a day with no transaction), but there's
                   * nothing there to select or click. */}
                  {hasTransaction && (
                    <Dot
                      cx={dotProps.cx}
                      cy={dotProps.cy}
                      r={isSelected ? 5 : 0}
                      fill={RUNNING_TOTAL_COLOR}
                      stroke="var(--paper)"
                      strokeWidth={2}
                    />
                  )}
                  {/* Invisible, larger hit-area so every point on the thin
                   * line is clickable, not just the pixel the line passes
                   * through — but only on days that actually had a
                   * transaction; a blank day has no dot and must not be
                   * clickable either. */}
                  {onPointClick && hasTransaction && (
                    <circle
                      cx={dotProps.cx}
                      cy={dotProps.cy}
                      r={12}
                      fill="transparent"
                      style={{ cursor: 'pointer' }}
                      onClick={handleClick}
                    />
                  )}
                </g>
              )
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
