import styles from './FilterBar.module.css'

interface ScopeToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
}

/** The "include transfers & income" switch, shared by Records and the
 * analytics pages (Time Series / Distribution) since all three accept
 * the same `include_excluded` query param. */
export function ScopeToggle({ checked, onChange, label = 'Include transfers & income' }: ScopeToggleProps) {
  return (
    <div className={styles.toggleField}>
      <span className={styles.fieldLabel}>Scope</span>
      <label className={styles.toggle}>
        <input
          type="checkbox"
          className={styles.checkboxInput}
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          data-testid="scope-toggle-input"
        />
        <span className={checked ? `${styles.switch} ${styles.switchOn}` : styles.switch} aria-hidden="true" />
        <span className={styles.toggleLabel}>{label}</span>
      </label>
    </div>
  )
}
