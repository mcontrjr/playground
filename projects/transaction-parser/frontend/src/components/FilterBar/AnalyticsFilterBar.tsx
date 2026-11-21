import { useAccounts } from '../../api/hooks/useAccounts'
import { useMonths } from '../../api/hooks/useTransactions'
import { DateRangePicker, type DateRange } from '../DateRangePicker/DateRangePicker'
import styles from './AnalyticsFilterBar.module.css'
import barStyles from './FilterBar.module.css'
import { FilterChipGroup } from './FilterChipGroup'
import { ScopeToggle } from './ScopeToggle'

export interface AnalyticsFilterState {
  accountIds: number[]
  includeExcluded: boolean
  /** Multi-selected month chips — same control as Records. Mutually
   * exclusive with `dateRange` (picking a range clears these and vice
   * versa); when both are empty the page falls back to its MonthSwiper
   * scope. */
  monthKeys: string[]
  /** Custom date range — overrides monthKeys and the page's MonthSwiper
   * scope when set. */
  dateRange?: DateRange
}

interface AnalyticsFilterBarProps {
  filters: AnalyticsFilterState
  onChange: (next: AnalyticsFilterState) => void
}

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

/** The filter affordances shared by Overview, Time Series, and
 * Distribution: month chips + a custom date-range picker (mutually
 * exclusive, same as Records — picking one clears the other), an
 * account chip group, and the transfers scope toggle (Income is
 * always included, not gated by this toggle). The page's MonthSwiper
 * stays alongside this for quick single-month nav; when monthKeys/
 * dateRange are both empty the page falls back to the swiper's scope.
 * Built on the same FilterChipGroup/ScopeToggle/DateRangePicker pieces
 * Records uses, so all pages stay visually and behaviorally
 * consistent. */
export function AnalyticsFilterBar({ filters, onChange }: AnalyticsFilterBarProps) {
  const { data: accounts } = useAccounts()
  const { data: months } = useMonths()
  const hasCustomRange = !!filters.dateRange
  const allMonthsSelected = (months ?? []).length > 0 && (months ?? []).every((m) => filters.monthKeys.includes(m.key))
  const hasActiveFilters =
    filters.accountIds.length > 0 || filters.includeExcluded || filters.monthKeys.length > 0 || hasCustomRange

  return (
    <div className={styles.bar}>
      <div className={styles.left}>
        <div className={barStyles.field}>
          <div className={barStyles.fieldLabelRow}>
            <span className={barStyles.fieldLabel}>Month</span>
            {!hasCustomRange && (months ?? []).length > 0 && (
              <span className={barStyles.groupActions}>
                {!allMonthsSelected && (
                  <button
                    type="button"
                    className={barStyles.groupActionButton}
                    onClick={() => onChange({ ...filters, monthKeys: (months ?? []).map((m) => m.key) })}
                  >
                    Select all
                  </button>
                )}
                {filters.monthKeys.length > 0 && (
                  <button
                    type="button"
                    className={barStyles.groupActionButton}
                    onClick={() => onChange({ ...filters, monthKeys: [] })}
                  >
                    Clear
                  </button>
                )}
              </span>
            )}
          </div>
          <div className={barStyles.multiSelect} role="group" aria-label="Filter by month">
            {(months ?? []).map((m) => {
              const isActive = filters.monthKeys.includes(m.key)
              return (
                <button
                  key={m.key}
                  type="button"
                  className={isActive ? `${barStyles.chip} ${barStyles.chipActive}` : barStyles.chip}
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
            {(months ?? []).length === 0 && <span className={barStyles.emptyHint}>None yet</span>}
            <DateRangePicker
              value={filters.dateRange}
              onChange={(dateRange) => onChange({ ...filters, dateRange, monthKeys: [] })}
              onClear={() => onChange({ ...filters, dateRange: undefined })}
            />
            {hasCustomRange && (
              <button
                type="button"
                className={barStyles.chip}
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

        {hasActiveFilters && (
          <button
            type="button"
            className={styles.clearButton}
            onClick={() =>
              onChange({ accountIds: [], includeExcluded: false, monthKeys: [], dateRange: undefined })
            }
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
