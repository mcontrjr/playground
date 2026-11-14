import type { ReactNode } from 'react'
import styles from './KpiTile.module.css'

interface KpiTileProps {
  label: string
  value: string
  tone?: 'neutral' | 'positive' | 'negative'
  sub?: ReactNode
}

/** The dark rounded tile — the one "solid" surface in the editorial
 * design language. Big light numerals, small uppercase label. */
export function KpiTile({ label, value, tone = 'neutral', sub }: KpiTileProps) {
  const valueClass =
    tone === 'positive' ? styles.valuePositive : tone === 'negative' ? styles.valueNegative : ''

  return (
    <div className={styles.tile} data-testid="kpi-tile" data-label={label}>
      <span className={styles.label}>{label}</span>
      <div>
        <div className={`${styles.value} ${valueClass}`} data-testid="kpi-tile-value">
          {value}
        </div>
        {sub && <div className={styles.sub}>{sub}</div>}
      </div>
    </div>
  )
}
