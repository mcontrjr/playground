import { useAccounts } from '../../api/hooks/useAccounts'
import { useCategories } from '../../api/hooks/useCategories'
import { useMonths } from '../../api/hooks/useTransactions'
import { DateRangePicker, type DateRange } from '../DateRangePicker/DateRangePicker'
import { FilterChipGroup } from './FilterChipGroup'
import styles from './FilterBar.module.css'
import { GroupedCategoryFilter } from './GroupedCategoryFilter'
import { ScopeToggle } from './ScopeToggle'
import { SearchInput } from './SearchInput'

export interface RecordsFilterState {
  accountIds: number[]
  categoryIds: number[]
  monthKeys: string[]
  search: string
  includeExcluded: boolean
  recurringOnly: boolean
  /** Custom date range — mutually exclusive with `monthKeys`:
   * applying a range clears month chips and vice versa. */
  dateRange?: DateRange
}

export const initialFilterState: RecordsFilterState = {
  accountIds: [],
  categoryIds: [],
  monthKeys: [],
  search: '',
  includeExcluded: false,
  recurringOnly: false,
}

interface FilterBarProps {
  filters: RecordsFilterState
  onChange: (next: RecordsFilterState) => void
  totalCount: number | undefined
  isLoading: boolean
  /** Hide the inline search input — RecordsPage renders its own
   * SearchInput directly above the table instead. */
  hideSearch?: boolean
}

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

export function FilterBar({ filters, onChange, totalCount, isLoading, hideSearch }: FilterBarProps) {
  const { data: accounts } = useAccounts()
  const { data: categories } = useCategories()
  const { data: months } = useMonths()

  const hasCustomRange = !!filters.dateRange
  const allMonthsSelected = (months ?? []).length > 0 && (months ?? []).every((m) => filters.monthKeys.includes(m.key))
  const hasActiveFilters =
    filters.accountIds.length > 0 ||
    filters.categoryIds.length > 0 ||
    filters.monthKeys.length > 0 ||
    !!filters.dateRange ||
    !!filters.search ||
    filters.includeExcluded ||
    filters.recurringOnly

  return (
    <div className={styles.bar}>
      <div className={styles.topRow}>
        {!hideSearch && (
          <SearchInput value={filters.search} onChange={(search) => onChange({ ...filters, search })} />
        )}

        <div className={styles.toggleGroup}>
          <ScopeToggle
            checked={filters.includeExcluded}
            onChange={(checked) => onChange({ ...filters, includeExcluded: checked })}
          />
          <ScopeToggle
            checked={filters.recurringOnly}
            onChange={(checked) => onChange({ ...filters, recurringOnly: checked })}
            label="Recurring only"
          />
        </div>
      </div>

      {hasActiveFilters && (
        <button
          type="button"
          className={styles.clearAllButton}
          onClick={() => onChange(initialFilterState)}
          data-testid="clear-all-filters"
        >
          Clear all filters
        </button>
      )}

      {/* Month, Account, then Category — stacked top-down. */}
      <div className={styles.chipGrid}>
        <div className={styles.field}>
          <div className={styles.fieldLabelRow}>
            <span className={styles.fieldLabel}>Month</span>
            {!hasCustomRange && (months ?? []).length > 0 && (
              <span className={styles.groupActions}>
                {!allMonthsSelected && (
                  <button
                    type="button"
                    className={styles.groupActionButton}
                    onClick={() => onChange({ ...filters, monthKeys: (months ?? []).map((m) => m.key) })}
                  >
                    Select all
                  </button>
                )}
                {filters.monthKeys.length > 0 && (
                  <button
                    type="button"
                    className={styles.groupActionButton}
                    onClick={() => onChange({ ...filters, monthKeys: [] })}
                  >
                    Clear
                  </button>
                )}
              </span>
            )}
          </div>
          <div className={styles.multiSelect} role="group" aria-label="Filter by month">
            {(months ?? []).map((m) => {
              const isActive = filters.monthKeys.includes(m.key)
              return (
                <button
                  key={m.key}
                  type="button"
                  className={isActive ? `${styles.chip} ${styles.chipActive}` : styles.chip}
                  disabled={hasCustomRange}
                  onClick={() =>
                    onChange({ ...filters, monthKeys: toggleInArray(filters.monthKeys, m.key) })
                  }
                  aria-pressed={isActive}
                >
                  {m.label}
                </button>
              )
            })}
            {(months ?? []).length === 0 && <span className={styles.emptyHint}>None yet</span>}
            <DateRangePicker
              value={filters.dateRange}
              onChange={(dateRange) => onChange({ ...filters, dateRange, monthKeys: [] })}
              onClear={() => onChange({ ...filters, dateRange: undefined })}
            />
            {hasCustomRange && (
              <button
                type="button"
                className={styles.chip}
                onClick={() => onChange({ ...filters, dateRange: undefined })}
                aria-label="Clear custom date range"
              >
                Custom range ✕
              </button>
            )}
          </div>
        </div>

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

        <GroupedCategoryFilter
          categories={categories ?? []}
          selected={filters.categoryIds}
          onToggle={(categoryId) =>
            onChange({ ...filters, categoryIds: toggleInArray(filters.categoryIds, categoryId) })
          }
          onSetSelection={(categoryIds) => onChange({ ...filters, categoryIds })}
        />
      </div>

      <p className={styles.resultCount} data-testid="records-result-count" data-count={totalCount ?? 0}>
        {isLoading ? (
          'Loading…'
        ) : (
          <>
            Showing <strong>{totalCount ?? 0}</strong> transaction{totalCount === 1 ? '' : 's'}
          </>
        )}
      </p>
    </div>
  )
}
