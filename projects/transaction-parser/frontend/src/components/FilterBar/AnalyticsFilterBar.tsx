import { useAccounts } from '../../api/hooks/useAccounts'
import styles from './AnalyticsFilterBar.module.css'
import { FilterChipGroup } from './FilterChipGroup'
import { ScopeToggle } from './ScopeToggle'

export interface AnalyticsFilterState {
  accountIds: number[]
  includeExcluded: boolean
}

interface AnalyticsFilterBarProps {
  filters: AnalyticsFilterState
  onChange: (next: AnalyticsFilterState) => void
}

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

/** The filter affordances shared by Time Series and Distribution: an
 * account chip group and the transfers scope toggle (Income is always
 * included, not gated by this toggle). Built on the same
 * FilterChipGroup/ScopeToggle pieces Records uses, so all three pages
 * stay visually and behaviorally consistent. */
export function AnalyticsFilterBar({ filters, onChange }: AnalyticsFilterBarProps) {
  const { data: accounts } = useAccounts()
  const hasActiveFilters = filters.accountIds.length > 0 || filters.includeExcluded

  return (
    <div className={styles.bar}>
      <div className={styles.left}>
        <FilterChipGroup
          label="Account"
          ariaLabel="Filter by account"
          options={(accounts ?? []).map((a) => ({ key: a.id, label: a.display_name }))}
          selected={filters.accountIds}
          onToggle={(key) =>
            onChange({ ...filters, accountIds: toggleInArray(filters.accountIds, Number(key)) })
          }
          onSetSelection={(keys) => onChange({ ...filters, accountIds: keys.map(Number) })}
        />
        {hasActiveFilters && (
          <button
            type="button"
            className={styles.clearButton}
            onClick={() => onChange({ accountIds: [], includeExcluded: false })}
            data-testid="clear-all-filters"
          >
            Clear all
          </button>
        )}
      </div>

      <ScopeToggle
        checked={filters.includeExcluded}
        onChange={(checked) => onChange({ ...filters, includeExcluded: checked })}
      />
    </div>
  )
}
