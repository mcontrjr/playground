import { useMemo } from 'react'
import { Bar, CartesianGrid, Cell, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DailyPoint } from '../../api/types'
import { buildRankedSeries, type PointGranularity, type SeriesRow } from './dailySeries'
import { ChartLegend } from './ChartLegend'
import { ChartTooltip, type ChartTooltipRow } from './ChartTooltip'
import { formatCurrency } from './format'
import styles from './CategoryBarsChart.module.css'

interface CategoryBarsChartProps {
  points: DailyPoint[]
  height?: number
  /** The currently-selected point's row key (date), or null. Dims
   * every other bar so the selection reads clearly against the
   * records panel below it. */
  selectedKey?: string | null
  onPointClick?: (dateKey: string) => void
  /** Whether `points` are per-day rows (per-month drill-down) or
   * per-month "YYYY-MM" rows (All records). Defaults to `'day'` to
   * match this component's original, only use case. */
  granularity?: PointGranularity
}

/** The daily/monthly stacked-category-spend half of what used to be
 * DailySeriesChart's dual-axis ComposedChart — split out so this half
 * can live visually above RunningTotalChart with its own single left
 * axis, and so a bar click can drive the day/month records panel
 * independently of the running-total line. */
export function CategoryBarsChart({
  points,
  height = 260,
  selectedKey,
  onPointClick,
  granularity = 'day',
}: CategoryBarsChartProps) {
  const { rows, stackKeys, colors, legendEntries } = useMemo(
    () => buildRankedSeries(points, granularity),
    [points, granularity],
  )

  return (
    <div className={styles.wrap}>
      <span className={styles.axisLabel}>Spend by category</span>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={rows}
          margin={{ top: 8, right: 8, left: 4, bottom: 4 }}
          barCategoryGap="20%"
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
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            width={56}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink-soft)' }}
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <Tooltip
            cursor={{ fill: 'var(--paper-sunk)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const categoryRows = payload.filter((p) => typeof p.value === 'number' && p.value > 0)
              if (categoryRows.length === 0) return null
              const tooltipRows: ChartTooltipRow[] = categoryRows
                .map((p) => ({
                  key: String(p.dataKey),
                  label: String(p.name),
                  value: Number(p.value),
                  color: String(p.color),
                }))
                .sort((a, b) => b.value - a.value)
              return <ChartTooltip heading={String(label)} rows={tooltipRows} showTotal />
            }}
          />
          {stackKeys.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              name={legendEntries.find((e) => e.key === key)?.label ?? key}
              stackId="spend"
              fill={colors[i]}
              stroke="var(--paper)"
              strokeWidth={1}
              maxBarSize={28}
              isAnimationActive={false}
              style={{ cursor: onPointClick ? 'pointer' : undefined }}
              onClick={(data) => {
                // Recharts' chart-level onClick + activeLabel reads from
                // Redux hover state that lags a render behind the actual
                // click (it's null on the very first click, and stale on
                // subsequent ones — a known upstream issue). Reading the
                // payload straight off the clicked Bar's own data avoids
                // that state entirely and is always in sync.
                const row = (data as { payload?: SeriesRow }).payload
                if (row && onPointClick) onPointClick(row.key)
              }}
            >
              {rows.map((row) => (
                <Cell
                  key={row.key}
                  opacity={selectedKey && selectedKey !== row.key ? 0.35 : 1}
                  style={{ cursor: onPointClick ? 'pointer' : undefined }}
                />
              ))}
            </Bar>
          ))}
        </ComposedChart>
      </ResponsiveContainer>
      <ChartLegend entries={legendEntries} />
    </div>
  )
}
