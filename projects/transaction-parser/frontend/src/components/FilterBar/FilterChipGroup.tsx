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
  /** Replaces the whole selection at once — backs the "Select all"/
   * "Clear" buttons. Optional so existing callers that don't need bulk
   * toggling (none currently) aren't forced to wire it up. */
  onSetSelection?: (keys: Array<string | number>) => void
  /** Keys with zero matching transactions under the *other* active
   * filters — dimmed (not disabled: still clickable, e.g. to clear a
   * now-empty selection) as a signal they'd currently contribute
   * nothing. Omit while facets haven't loaded yet, so nothing dims
   * before there's data to judge it against. */
  unavailableKeys?: Set<string | number>
}

/** The pill multiselect used for month/account/category filters —
 * extracted so Records' FilterBar and any other filter surface share
 * one implementation instead of three near-identical copies. */
export function FilterChipGroup({
  label,
  options,
  selected,
  onToggle,
  ariaLabel,
  onSetSelection,
  unavailableKeys,
}: FilterChipGroupProps) {
  const allSelected = options.length > 0 && options.every((o) => selected.includes(o.key))

  return (
    <div className={styles.field}>
      <div className={styles.fieldLabelRow}>
        <span className={styles.fieldLabel}>{label}</span>
        {onSetSelection && options.length > 0 && (
          <span className={styles.groupActions}>
            {!allSelected && (
              <button
                type="button"
                className={styles.groupActionButton}
                onClick={() => onSetSelection(options.map((o) => o.key))}
              >
                Select all
              </button>
            )}
            {selected.length > 0 && (
              <button type="button" className={styles.groupActionButton} onClick={() => onSetSelection([])}>
                Clear
              </button>
            )}
          </span>
        )}
      </div>
      <div className={styles.multiSelect} role="group" aria-label={ariaLabel}>
        {options.map((option) => {
          const isActive = selected.includes(option.key)
          const isUnavailable = !!unavailableKeys?.has(option.key)
          return (
            <button
              key={option.key}
              type="button"
              className={[
                styles.chip,
                isActive ? styles.chipActive : '',
                isUnavailable ? styles.chipUnavailable : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => onToggle(option.key)}
              aria-pressed={isActive}
              title={isUnavailable ? 'No matching transactions with the current filters' : undefined}
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
