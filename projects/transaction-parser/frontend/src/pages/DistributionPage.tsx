import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { useAnalyticsDistribution } from '../api/hooks/useAnalytics'
import { useMonthScope } from '../hooks/useMonthScope'
import { AnalyticsFilterBar, type AnalyticsFilterState } from '../components/FilterBar/AnalyticsFilterBar'
import { DonutChart } from '../components/charts/DonutChart'
import { formatCurrency, formatPercent } from '../components/charts/format'
import { assignSeriesColors, OTHER_LABEL } from '../components/charts/palette'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import { RecordsPanel } from '../components/RecordsPanel/RecordsPanel'
import styles from './DistributionPage.module.css'

const DEFAULT_FILTERS: AnalyticsFilterState = { accountIds: [], includeExcluded: false }

export function DistributionPage() {
  const [filters, setFilters] = usePreference<AnalyticsFilterState>('filters:distribution', DEFAULT_FILTERS)
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)
  const scope = useMonthScope()

  const { data, isLoading } = useAnalyticsDistribution({
    date_from: scope.dateFrom,
    date_to: scope.dateTo,
    account_ids: filters.accountIds.length ? filters.accountIds : undefined,
    include_excluded: filters.includeExcluded,
  })

  const slices = useMemo(() => {
    if (!data) return []
    const sorted = [...data.entries].sort((a, b) => Number(b.amount) - Number(a.amount))
    const colors = assignSeriesColors(Math.min(sorted.length, 9))
    const kept = sorted.slice(0, 8).map((entry, i) => ({
      key: String(entry.category_id),
      label: entry.name,
      value: Number(entry.amount),
      color: colors[i]!,
      categoryId: entry.category_id as number | null,
    }))
    if (sorted.length > 8) {
      const rest = sorted.slice(8)
      const otherValue = rest.reduce((sum, e) => sum + Number(e.amount), 0)
      kept.push({
        key: '__other__',
        label: OTHER_LABEL,
        value: otherValue,
        color: colors[8] ?? colors[7]!,
        categoryId: null,
      })
    }
    return kept
  }, [data])

  const total = Number(data?.total ?? 0)
  const hasData = slices.length > 0 && total > 0

  const selectedSlice = slices.find((s) => s.categoryId === selectedCategoryId) ?? null

  const handleRowClick = (categoryId: number | null) => {
    if (categoryId == null) return
    setSelectedCategoryId((current) => (current === categoryId ? null : categoryId))
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Distribution</h1>
        <p className={styles.subtitle}>Where the money goes — transfers and income excluded unless toggled on.</p>
      </header>

      <AnalyticsFilterBar filters={filters} onChange={setFilters} />

      <MonthSwiper
        label={scope.label}
        canGoNewer={scope.canGoNewer}
        canGoOlder={scope.canGoOlder}
        badge={scope.isAll ? 'Entire history' : 'Month view'}
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
              const isClickable = slice.categoryId != null
              const isSelected = isClickable && slice.categoryId === selectedCategoryId
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
                  onClick={() => handleRowClick(slice.categoryId)}
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

      {selectedSlice && selectedSlice.categoryId != null && (
        <RecordsPanel
          title={selectedSlice.label}
          filters={{
            category_ids: [selectedSlice.categoryId],
            date_from: scope.dateFrom,
            date_to: scope.dateTo,
            account_ids: filters.accountIds.length ? filters.accountIds : undefined,
            include_excluded: filters.includeExcluded,
          }}
          onClose={() => setSelectedCategoryId(null)}
        />
      )}
    </div>
  )
}
