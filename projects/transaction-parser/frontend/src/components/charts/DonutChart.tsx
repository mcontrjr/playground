import { useMemo } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ChartTooltip } from './ChartTooltip'
import { formatCurrency } from './format'
import styles from './DonutChart.module.css'

export interface DonutSlice {
  key: string
  label: string
  value: number
  color: string
}

interface DonutChartProps {
  slices: DonutSlice[]
  total: number
  centerLabel?: string
  height?: number
  /** Highlights one slice (hover-sync with the side list). */
  activeKey?: string | null
  onHoverSlice?: (key: string | null) => void
}

export function DonutChart({
  slices,
  total,
  centerLabel = 'Total spent',
  height = 300,
  activeKey,
  onHoverSlice,
}: DonutChartProps) {
  const data = useMemo(() => slices, [slices])

  return (
    <div className={styles.wrap}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius="62%"
            outerRadius="92%"
            paddingAngle={data.length > 1 ? 1.5 : 0}
            stroke="var(--paper)"
            strokeWidth={2}
            onMouseEnter={(_, index) => onHoverSlice?.(data[index]?.key ?? null)}
            onMouseLeave={() => onHoverSlice?.(null)}
          >
            {data.map((slice) => (
              <Cell
                key={slice.key}
                fill={slice.color}
                opacity={activeKey && activeKey !== slice.key ? 0.35 : 1}
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const p = payload[0]
              const value = Number(p?.value ?? 0)
              return (
                <ChartTooltip
                  rows={[
                    {
                      key: String(p?.name),
                      label: String(p?.name),
                      value,
                      color: String((p?.payload as DonutSlice)?.color),
                    },
                  ]}
                />
              )
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className={styles.center}>
        <div className={styles.centerValue}>{formatCurrency(total)}</div>
        <div className={styles.centerLabel}>{centerLabel}</div>
      </div>
    </div>
  )
}
