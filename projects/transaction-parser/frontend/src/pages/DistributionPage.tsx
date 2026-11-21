import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { useAnalyticsDistribution } from '../api/hooks/useAnalytics'
import { useMonths } from '../api/hooks/useTransactions'
import { useMonthScope } from '../hooks/useMonthScope'
import { deriveDateRange } from '../hooks/deriveDateRange'
import { AnalyticsFilterBar, type AnalyticsFilterState } from '../components/FilterBar/AnalyticsFilterBar'
import { DonutChart } from '../components/charts/DonutChart'
import { formatCurrency, formatPercent } from '../components/charts/format'
import { assignDistributionColors, MAX_DISTRIBUTION_SLOTS, OTHER_LABEL } from '../components/charts/palette'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import { RecordsPanel } from '../components/RecordsPanel/RecordsPanel'
import styles from './DistributionPage.module.css'

const DEFAULT_FILTERS: AnalyticsFilterState = {
  accountIds: [],
  includeExcluded: false,
  monthKeys: [],
  dateRange: undefined,
}

export function DistributionPage() {
  const [filters, setFilters] = usePreference<AnalyticsFilterState>('filters:distribution', DEFAULT_FILTERS)
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const scope = useMonthScope()
  const { data: months } = useMonths()

  const hasCustomRange = !!filters.dateRange
  const hasMonthOverride = hasCustomRange || filters.monthKeys.length > 0
  const resolved = deriveDateRange(filters, months ?? [])
  const dateFrom = resolved.date_from ?? scope.dateFrom
  const dateTo = resolved.date_to ?? scope.dateTo

  const { data, isLoading } = useAnalyticsDistribution({
    date_from: dateFrom,
    date_to: dateTo,
    account_ids: filters.accountIds.length ? filters.accountIds : undefined,
    include_excluded: filters.includeExcluded,
  })

  const slices = useMemo(() => {
    if (!data) return []
    const sorted = [...data.entries].sort((a, b) => Number(b.amount) - Number(a.amount))
    const colors = assignDistributionColors(Math.min(sorted.length, MAX_DISTRIBUTION_SLOTS + 1))
    const kept = sorted.slice(0, MAX_DISTRIBUTION_SLOTS).map((entry, i) => ({
      key: String(entry.category_id),
      label: entry.name,
      value: Number(entry.amount),
      color: colors[i]!,
      categoryIds: entry.category_id != null ? [entry.category_id] : [],
    }))
    if (sorted.length > MAX_DISTRIBUTION_SLOTS) {
      const rest = sorted.slice(MAX_DISTRIBUTION_SLOTS)
      const otherValue = rest.reduce((sum, e) => sum + Number(e.amount), 0)
      kept.push({
        key: '__other__',
        label: OTHER_LABEL,
        value: otherValue,
        color: colors[MAX_DISTRIBUTION_SLOTS] ?? colors[MAX_DISTRIBUTION_SLOTS - 1]!,
        // Everything past the top 12, folded into one slice — drilling
        // into it filters by all of their category ids at once rather
        // than being disabled, since there's no single category to
        // point at.
        categoryIds: rest.map((e) => e.category_id).filter((id): id is number => id != null),
      })
    }
    return kept
  }, [data])

  const total = Number(data?.total ?? 0)
  const hasData = slices.length > 0 && total > 0

  const selectedSlice = slices.find((s) => s.key === selectedKey) ?? null

  const handleRowClick = (key: string, categoryIds: number[]) => {
    if (categoryIds.length === 0) return
    setSelectedKey((current) => (current === key ? null : key))
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Distribution</h1>
        <p className={styles.subtitle}>Where the money goes — transfers excluded unless toggled on.</p>
      </header>

      <AnalyticsFilterBar filters={filters} onChange={setFilters} />

      <MonthSwiper
        label={hasCustomRange ? 'Custom range' : hasMonthOverride ? 'Month filter' : scope.label}
        canGoNewer={!hasMonthOverride && scope.canGoNewer}
        canGoOlder={!hasMonthOverride && scope.canGoOlder}
        badge={hasMonthOverride ? undefined : scope.isAll ? 'Entire history' : 'Month view'}
        onNewer={scope.goNewer}
        onOlder={scope.goOlder}
      />

      {isLoading ? (
        <p className={styles.empty}>Loading…</p>
      ) : hasData ? (
        <div className={styles.layout}>
          <DonutChart
            slices={slices}
            total={total}
            activeKey={activeKey}
            onHoverSlice={setActiveKey}
          />
          <div className={styles.list}>
            {slices.map((slice) => {
              const isClickable = slice.categoryIds.length > 0
              const isSelected = isClickable && slice.key === selectedKey
              return (
                <button
                  key={slice.key}
                  type="button"
                  className={[
                    styles.row,
                    activeKey && activeKey !== slice.key ? styles.rowMuted : '',
                    isSelected ? styles.rowSelected : '',
                    isClickable ? '' : styles.rowDisabled,
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onMouseEnter={() => setActiveKey(slice.key)}
                  onMouseLeave={() => setActiveKey(null)}
                  onClick={() => handleRowClick(slice.key, slice.categoryIds)}
                  disabled={!isClickable}
                  aria-pressed={isSelected}
                  data-testid="distribution-row"
                  data-label={slice.label}
                >
                  <span className={styles.swatch} style={{ background: slice.color }} />
                  <span className={styles.name}>{slice.label}</span>
                  <span className={styles.percent}>{formatPercent(slice.value / total)}</span>
                  <span className={styles.amount}>{formatCurrency(slice.value)}</span>
                </button>
              )
            })}
          </div>
        </div>
      ) : (
        <p className={styles.empty}>No categorized spend in this range yet.</p>
      )}

      {selectedSlice && selectedSlice.categoryIds.length > 0 && (
        <RecordsPanel
          title={selectedSlice.label}
          filters={{
            category_ids: selectedSlice.categoryIds,
            date_from: dateFrom,
            date_to: dateTo,
            account_ids: filters.accountIds.length ? filters.accountIds : undefined,
            include_excluded: filters.includeExcluded,
          }}
          onClose={() => setSelectedKey(null)}
        />
      )}
    </div>
  )
}
