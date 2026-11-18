import { useMemo } from 'react'
import { Bar, CartesianGrid, Cell, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DailyPoint } from '../../api/types'
import { formatDay } from './dailySeries'
import type { PointGranularity } from './dailySeries'
import { ChartTooltip } from './ChartTooltip'
import { formatCurrency, formatMonthPeriod } from './format'
import styles from './NetDayChart.module.css'

interface NetRow {
  key: string
  label: string
  net: number
}

const POSITIVE_COLOR = 'var(--accent-positive)'
const NEGATIVE_COLOR = 'var(--accent-negative)'

function formatLabel(key: string, granularity: PointGranularity): string {
  return granularity === 'month' ? formatMonthPeriod(key) : formatDay(key)
}

interface NetDayChartProps {
  points: DailyPoint[]
  height?: number
  selectedKey?: string | null
  onPointClick?: (dateKey: string) => void
  granularity?: PointGranularity
}

/** Each point's NET total (income minus spend, signed) as a bar
 * centered at zero — green above the axis on a net-positive day/month,
 * red below on a net-negative one. Distinct from CategoryBarsChart
 * (which only stacks OUTFLOWS broken down by category): this chart
 * answers "did this day/month come out ahead or behind overall",
 * which a spend-only breakdown can't show — a big-income, big-spend
 * day and a big-income, no-spend day look identical in the spend
 * chart but very different here. */
export function NetDayChart({
  points,
  height = 180,
  selectedKey,
  onPointClick,
  granularity = 'day',
}: NetDayChartProps) {
  const rows = useMemo<NetRow[]>(
    () => points.map((p) => ({ key: p.date, label: formatLabel(p.date, granularity), net: Number(p.value) })),
    [points, granularity],
  )

  return (
    <div className={styles.wrap}>
      <span className={styles.axisLabel}>Net (income − spend)</span>
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
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            width={56}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink-soft)' }}
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <ReferenceLine y={0} stroke="var(--chart-axis)" />
          <Tooltip
            cursor={{ fill: 'var(--paper-sunk)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const row = payload[0]
              if (row?.value == null) return null
              const net = Number(row.value)
              return (
                <ChartTooltip
                  heading={String(label)}
                  rows={[
                    {
                      key: 'net',
                      label: 'Net',
                      value: net,
                      color: net >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR,
                    },
                  ]}
                />
              )
            }}
          />
          <Bar
            dataKey="net"
            name="Net"
            maxBarSize={28}
            isAnimationActive={false}
            style={{ cursor: onPointClick ? 'pointer' : undefined }}
            onClick={(data) => {
              const row = (data as { payload?: NetRow }).payload
              if (row && onPointClick) onPointClick(row.key)
            }}
          >
            {rows.map((row) => (
              <Cell
                key={row.key}
                fill={row.net >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR}
                opacity={selectedKey && selectedKey !== row.key ? 0.35 : 1}
                style={{ cursor: onPointClick ? 'pointer' : undefined }}
              />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
