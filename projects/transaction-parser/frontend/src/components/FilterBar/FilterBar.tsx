import { useEffect, useState } from 'react'
import { useAccounts } from '../../api/hooks/useAccounts'
import { useCategories } from '../../api/hooks/useCategories'
import { useMonths } from '../../api/hooks/useTransactions'
import { FilterChipGroup } from './FilterChipGroup'
import styles from './FilterBar.module.css'
import { GroupedCategoryFilter } from './GroupedCategoryFilter'
import { ScopeToggle } from './ScopeToggle'
import { useDebouncedValue } from './useDebouncedValue'

export interface RecordsFilterState {
  accountIds: number[]
  categoryIds: number[]
  monthKeys: string[]
  search: string
  includeExcluded: boolean
  recurringOnly: boolean
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
}

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

export function FilterBar({ filters, onChange, totalCount, isLoading }: FilterBarProps) {
  const { data: accounts } = useAccounts()
  const { data: categories } = useCategories()
  const { data: months } = useMonths()
  const [searchInput, setSearchInput] = useState(filters.search)
  const debouncedSearch = useDebouncedValue(searchInput, 350)

  // Propagate the debounced search value once it settles.
  useEffect(() => {
    if (debouncedSearch !== filters.search) {
      onChange({ ...filters, search: debouncedSearch })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  return (
    <div className={styles.bar}>
      <div className={styles.topRow}>
        <div className={styles.field}>
          <label className={styles.fieldLabel} htmlFor="records-search">
            Search
          </label>
          <input
            id="records-search"
            className={styles.search}
            type="search"
            placeholder="Description contains…"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </div>

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

      {/* Month, Account, then Category — stacked top-down. */}
      <div className={styles.chipGrid}>
        <FilterChipGroup
          label="Month"
          ariaLabel="Filter by month"
          options={(months ?? []).map((m) => ({ key: m.key, label: m.label }))}
          selected={filters.monthKeys}
          onToggle={(key) =>
            onChange({ ...filters, monthKeys: toggleInArray(filters.monthKeys, String(key)) })
          }
        />

        <FilterChipGroup
          label="Account"
          ariaLabel="Filter by account"
          options={(accounts ?? []).map((a) => ({ key: a.id, label: a.display_name }))}
          selected={filters.accountIds}
          onToggle={(key) =>
            onChange({ ...filters, accountIds: toggleInArray(filters.accountIds, Number(key)) })
          }
        />

        <GroupedCategoryFilter
          categories={categories ?? []}
          selected={filters.categoryIds}
          onToggle={(categoryId) =>
            onChange({ ...filters, categoryIds: toggleInArray(filters.categoryIds, categoryId) })
          }
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
