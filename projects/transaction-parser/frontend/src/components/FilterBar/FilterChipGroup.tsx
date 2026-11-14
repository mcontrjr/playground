import styles from './FilterBar.module.css'

export interface ChipOption {
  key: string | number
  label: string
}

interface FilterChipGroupProps {
  label: string
  options: ChipOption[]
  selected: Array<string | number>
  onToggle: (key: string | number) => void
  ariaLabel: string
}

/** The pill multiselect used for month/account/category filters —
 * extracted so Records' FilterBar and any other filter surface share
 * one implementation instead of three near-identical copies. */
export function FilterChipGroup({ label, options, selected, onToggle, ariaLabel }: FilterChipGroupProps) {
  return (
    <div className={styles.field}>
      <span className={styles.fieldLabel}>{label}</span>
      <div className={styles.multiSelect} role="group" aria-label={ariaLabel}>
        {options.map((option) => {
          const isActive = selected.includes(option.key)
          return (
            <button
              key={option.key}
              type="button"
              className={isActive ? `${styles.chip} ${styles.chipActive}` : styles.chip}
              onClick={() => onToggle(option.key)}
              aria-pressed={isActive}
            >
              {option.label}
            </button>
          )
        })}
        {options.length === 0 && <span className={styles.emptyHint}>None yet</span>}
      </div>
    </div>
  )
}
