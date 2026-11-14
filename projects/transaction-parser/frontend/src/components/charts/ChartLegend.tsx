import styles from './ChartLegend.module.css'

export interface LegendEntry {
  key: string
  label: string
  color: string
}

interface ChartLegendProps {
  entries: LegendEntry[]
  /** When provided, entries become hoverable/clickable (used for the
   * distribution donut's list-chart hover sync). */
  activeKey?: string | null
  onHover?: (key: string | null) => void
}

export function ChartLegend({ entries, activeKey, onHover }: ChartLegendProps) {
  const interactive = Boolean(onHover)

  return (
    <div className={styles.legend} role="list">
      {entries.map((entry) => {
        const muted = interactive && activeKey != null && activeKey !== entry.key
        return (
          <button
            key={entry.key}
            type="button"
            role="listitem"
            className={`${styles.item} ${interactive ? styles.itemInteractive : ''} ${
              muted ? styles.itemMuted : ''
            }`}
            onMouseEnter={() => onHover?.(entry.key)}
            onMouseLeave={() => onHover?.(null)}
            disabled={!interactive}
          >
            <span className={styles.swatch} style={{ background: entry.color }} />
            {entry.label}
          </button>
        )
      })}
    </div>
  )
}
