import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ChartTooltip, type ChartTooltipRow } from './ChartTooltip'
import { formatCurrency } from './format'
import { assignSeriesColors, OTHER_LABEL } from './palette'
import styles from './StackedBarChart.module.css'

export interface StackedBarSeries {
  key: string
  name: string
  /** One value per period, aligned to `periods`. Already absolute
   * (spend magnitudes), not signed. */
  values: number[]
}

interface StackedBarChartProps {
  periods: string[]
  periodLabels: string[]
  series: StackedBarSeries[]
  height?: number
}

/** Collapses series past the 8 safe categorical slots into a shared
 * "Other" series, summed per period — the dataviz rule that a 9th+
 * category never invents a new hue. */
function foldIntoOther(series: StackedBarSeries[], periods: string[]): StackedBarSeries[] {
  if (series.length <= 8) return series
  const kept = series.slice(0, 8)
  const rest = series.slice(8)
  const otherValues = periods.map((_, i) => rest.reduce((sum, s) => sum + (s.values[i] ?? 0), 0))
  return [...kept, { key: '__other__', name: OTHER_LABEL, values: otherValues }]
}

export function StackedBarChart({ periods, periodLabels, series, height = 320 }: StackedBarChartProps) {
  const folded = useMemo(() => foldIntoOther(series, periods), [series, periods])
  const colors = useMemo(() => assignSeriesColors(folded.length), [folded.length])

  const rows = useMemo(
    () =>
      periods.map((period, i) => {
        const row: Record<string, number | string> = { period, label: periodLabels[i] ?? period }
        for (const s of folded) row[s.key] = s.values[i] ?? 0
        return row
      }),
    [periods, periodLabels, folded],
  )

  return (
    <div className={styles.wrap}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={rows} margin={{ top: 4, right: 4, left: 4, bottom: 4 }} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="0" />
          <XAxis
            dataKey="label"
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink)' }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            width={56}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink)' }}
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <Tooltip
            cursor={{ fill: 'var(--paper-sunk)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const tooltipRows: ChartTooltipRow[] = payload
                .filter((p) => typeof p.value === 'number' && p.value > 0)
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
          {folded.map((s, i) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.name}
              stackId="spend"
              fill={colors[i]}
              stroke="var(--paper)"
              strokeWidth={2}
              maxBarSize={40}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
