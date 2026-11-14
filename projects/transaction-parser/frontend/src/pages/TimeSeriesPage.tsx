import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { useAnalyticsMonthlyDaily } from '../api/hooks/useAnalytics'
import { useMonths } from '../api/hooks/useTransactions'
import { AnalyticsFilterBar, type AnalyticsFilterState } from '../components/FilterBar/AnalyticsFilterBar'
import { DailySeriesChart } from '../components/charts/DailySeriesChart'
import { formatCurrency } from '../components/charts/format'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import styles from './TimeSeriesPage.module.css'

const DEFAULT_FILTERS: AnalyticsFilterState = { accountIds: [], includeExcluded: false }

export function TimeSeriesPage() {
  const [filters, setFilters] = usePreference<AnalyticsFilterState>('filters:time-series', DEFAULT_FILTERS)
  const { data: months } = useMonths()

  // Index into `months` (descending, most-recent-first); 0 = latest.
  // Deliberately NOT reset when `filters` changes — switching an
  // account/scope filter should re-fetch the same month's data under
  // the new filter, not snap the user back to the current month.
  const [monthIndex, setMonthIndex] = useState(0)

  const activeMonth = months?.[monthIndex]

  const { data, isLoading } = useAnalyticsMonthlyDaily(activeMonth?.from ?? '', {
    account_ids: filters.accountIds.length ? filters.accountIds : undefined,
    include_excluded: filters.includeExcluded,
  })

  const isLatest = monthIndex === 0
  const canGoOlder = !!months && monthIndex < months.length - 1

  const monthTotal = useMemo(() => (data ? formatCurrency(data.month_total) : null), [data])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Time Series</h1>
        <p className={styles.subtitle}>Daily spend for one month at a time — swipe or use the arrows to go back.</p>
      </header>

      <AnalyticsFilterBar filters={filters} onChange={setFilters} />

      {activeMonth ? (
        <MonthSwiper
          label={data?.label ?? activeMonth.label}
          isLatest={isLatest}
          canGoOlder={canGoOlder}
          onNewer={() => setMonthIndex((i) => Math.max(0, i - 1))}
          onOlder={() => setMonthIndex((i) => (months ? Math.min(months.length - 1, i + 1) : i))}
        />
      ) : null}

      <div className={styles.chartWrap}>
        {isLoading ? (
          <p className={styles.empty}>Loading…</p>
        ) : data && data.points.length > 0 ? (
          <>
            <DailySeriesChart points={data.points} />
            <div className={styles.monthTotal}>
              <span className={styles.monthTotalLabel}>Month total </span>
              <span className={styles.monthTotalValue}>{monthTotal}</span>
            </div>
          </>
        ) : (
          <p className={styles.empty}>No spend in this month yet.</p>
        )}
      </div>
    </div>
  )
}
