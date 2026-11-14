import styles from './ChartTooltip.module.css'
import { formatCurrencyPrecise } from './format'

export interface ChartTooltipRow {
  key: string
  label: string
  value: number
  color: string
}

interface ChartTooltipProps {
  heading?: string
  rows: ChartTooltipRow[]
  /** Shows a summed total row beneath the entries (e.g. month total). */
  showTotal?: boolean
}

/** The dark tile-colored tooltip shared by every chart in the kit — a
 * quiet, consistent surface rather than Recharts' default white box
 * with a drop shadow. */
export function ChartTooltip({ heading, rows, showTotal }: ChartTooltipProps) {
  if (rows.length === 0) return null
  const total = rows.reduce((sum, row) => sum + row.value, 0)

  return (
    <div className={styles.tooltip}>
      {heading && <div className={styles.heading}>{heading}</div>}
      {rows.map((row) => (
        <div className={styles.row} key={row.key}>
          <span className={styles.rowLabel}>
            <span className={styles.swatch} style={{ background: row.color }} />
            <span className={styles.name}>{row.label}</span>
          </span>
          <span className={styles.value}>{formatCurrencyPrecise(row.value)}</span>
        </div>
      ))}
      {showTotal && rows.length > 1 && (
        <div className={styles.total}>
          <span>Total</span>
          <span className={styles.value}>{formatCurrencyPrecise(total)}</span>
        </div>
      )}
    </div>
  )
}
