import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis } from 'recharts'
import { formatCurrency } from './format'
import styles from './MiniBarChart.module.css'

export interface MiniBarPoint {
  label: string
  value: number
}

interface MiniBarChartProps {
  data: MiniBarPoint[]
  height?: number
}

/** A quiet monthly-spend bar strip for the Overview page — total spend
 * per month, ink-colored (this view isn't categorical, so no series
 * palette applies). No hover/tooltip/cursor interaction: the amount is
 * printed directly above each bar instead, so there's nothing to
 * glitch when a click lands on a bar. */
export function MiniBarChart({ data, height = 120 }: MiniBarChartProps) {
  return (
    <div className={styles.wrap}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 20, right: 4, left: 4, bottom: 0 }} barCategoryGap="32%">
          <XAxis
            dataKey="label"
            axisLine={{ stroke: 'var(--chart-axis)' }}
            tickLine={false}
            tick={{ fontFamily: 'var(--font-sans)', fontSize: 11, fill: 'var(--ink)' }}
          />
          <Bar dataKey="value" fill="var(--ink)" radius={[3, 3, 0, 0]} maxBarSize={28} isAnimationActive={false}>
            <LabelList
              dataKey="value"
              position="top"
              formatter={(value: unknown) =>
                typeof value === 'number' || typeof value === 'string' ? formatCurrency(Number(value)) : ''
              }
              style={{ fill: 'var(--ink)', fontFamily: 'var(--font-sans)', fontSize: 11 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
