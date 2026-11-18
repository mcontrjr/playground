import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { useAnalyticsMonthlyDaily, useAnalyticsTimeseries } from '../api/hooks/useAnalytics'
import { useMonthScope } from '../hooks/useMonthScope'
import { AnalyticsFilterBar, type AnalyticsFilterState } from '../components/FilterBar/AnalyticsFilterBar'
import { CategoryBarsChart } from '../components/charts/CategoryBarsChart'
import { NetDayChart } from '../components/charts/NetDayChart'
import { RunningTotalChart } from '../components/charts/RunningTotalChart'
import { formatCurrency, formatMonthPeriod } from '../components/charts/format'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import { RecordsPanel } from '../components/RecordsPanel/RecordsPanel'
import type { DailyPoint, TimeseriesResponse } from '../api/types'
import styles from './TimeSeriesPage.module.css'

const DEFAULT_FILTERS: AnalyticsFilterState = { accountIds: [], includeExcluded: false }

/** Converts the monthly `TimeseriesResponse` (one value per category
 * per period) into the same `DailyPoint[]` shape `CategoryBarsChart`/
 * `RunningTotalChart` already consume for the per-month daily view —
 * so "All" mode reuses the exact same chart components and top-8
 * capping instead of a parallel implementation, with `date` holding
 * the period key ("YYYY-MM") rather than an ISO day. */
function timeseriesToPoints(data: TimeseriesResponse): DailyPoint[] {
  let running = 0
  return data.periods.map((period) => {
    const byCategory = data.series
      .map((series) => {
        const point = series.values.find((v) => v.period === period)
        return { category_id: series.category_id, name: series.name, amount: point?.value ?? '0' }
      })
      .filter((entry) => Number(entry.amount) !== 0)
    const periodTotal = byCategory.reduce((sum, e) => sum + Number(e.amount), 0)
    running += periodTotal
    return {
      date: period,
      value: String(periodTotal),
      running_total: String(running),
      by_category: byCategory,
    }
  })
}

type ClickSource = 'bars' | 'net' | 'running'

export function TimeSeriesPage() {
  const [filters, setFilters] = usePreference<AnalyticsFilterState>('filters:time-series', DEFAULT_FILTERS)
  const scope = useMonthScope()
  const [selected, setSelected] = useState<{ dateKey: string; source: ClickSource } | null>(null)

  const analyticsFilters = {
    account_ids: filters.accountIds.length ? filters.accountIds : undefined,
    include_excluded: filters.includeExcluded,
  }

  const monthlyDaily = useAnalyticsMonthlyDaily(scope.month?.from ?? '', analyticsFilters, {
    enabled: !scope.isAll,
  })
  const allTime = useAnalyticsTimeseries('month', { ...analyticsFilters })

  const isLoading = scope.isAll ? allTime.isLoading : monthlyDaily.isLoading
  const points = useMemo<DailyPoint[]>(() => {
    if (scope.isAll) return allTime.data ? timeseriesToPoints(allTime.data) : []
    return monthlyDaily.data?.points ?? []
  }, [scope.isAll, allTime.data, monthlyDaily.data])

  const total = useMemo(() => {
    if (scope.isAll) return points.reduce((sum, p) => sum + Number(p.value), 0)
    return monthlyDaily.data ? Number(monthlyDaily.data.month_total) : null
  }, [scope.isAll, points, monthlyDaily.data])

  // Clicking the same point on the same chart toggles its panel closed;
  // clicking any other point (same or different chart) opens that
  // chart's panel instead, closing whichever one was open before —
  // only one panel is ever open across all three charts.
  const handlePointClick = (source: ClickSource) => (dateKey: string) => {
    setSelected((current) =>
      current?.dateKey === dateKey && current.source === source ? null : { dateKey, source },
    )
  }

  const panelFilters = useMemo(() => {
    if (!selected) return null
    const accountIds = filters.accountIds.length ? filters.accountIds : undefined
    if (scope.isAll) {
      // selected.dateKey is a "YYYY-MM" period in All mode — scope the
      // panel to that whole month.
      const [year, month] = selected.dateKey.split('-').map(Number)
      const from = `${selected.dateKey}-01`
      const lastDay = new Date(year!, month!, 0).getDate()
      const to = `${selected.dateKey}-${String(lastDay).padStart(2, '0')}`
      return { date_from: from, date_to: to, account_ids: accountIds, include_excluded: filters.includeExcluded }
    }
    return {
      date_from: selected.dateKey,
      date_to: selected.dateKey,
      account_ids: accountIds,
      include_excluded: filters.includeExcluded,
    }
  }, [selected, scope.isAll, filters])

  const panelTitle = useMemo(() => {
    if (!selected) return ''
    return scope.isAll ? formatMonthPeriod(selected.dateKey) : selected.dateKey
  }, [selected, scope.isAll])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Time Series</h1>
        <p className={styles.subtitle}>
          Swipe or use the arrows to move between all-time and individual months. Click a bar or point
          to see the records behind it.
        </p>
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

      <div className={styles.chartWrap}>
        {isLoading ? (
          <p className={styles.empty}>Loading…</p>
        ) : points.length > 0 ? (
          <>
            <CategoryBarsChart
              points={points}
              selectedKey={selected?.source === 'bars' ? selected.dateKey : null}
              onPointClick={handlePointClick('bars')}
              granularity={scope.isAll ? 'month' : 'day'}
            />

            {selected?.source === 'bars' && panelFilters && (
              <RecordsPanel title={panelTitle} filters={panelFilters} onClose={() => setSelected(null)} />
            )}

            <NetDayChart
              points={points}
              selectedKey={selected?.source === 'net' ? selected.dateKey : null}
              onPointClick={handlePointClick('net')}
              granularity={scope.isAll ? 'month' : 'day'}
            />

            {selected?.source === 'net' && panelFilters && (
              <RecordsPanel title={panelTitle} filters={panelFilters} onClose={() => setSelected(null)} />
            )}

            <RunningTotalChart
              points={points}
              selectedKey={selected?.source === 'running' ? selected.dateKey : null}
              onPointClick={handlePointClick('running')}
              granularity={scope.isAll ? 'month' : 'day'}
              monthBounds={
                !scope.isAll && scope.month ? { from: scope.month.from, to: scope.month.to } : undefined
              }
            />

            {selected?.source === 'running' && panelFilters && (
              <RecordsPanel title={panelTitle} filters={panelFilters} onClose={() => setSelected(null)} />
            )}

            {total != null && (
              <div className={styles.monthTotal}>
                <span className={styles.monthTotalLabel}>{scope.isAll ? 'All-time total ' : 'Month total '}</span>
                <span className={styles.monthTotalValue}>{formatCurrency(total)}</span>
              </div>
            )}
          </>
        ) : (
          <p className={styles.empty}>No spend in this range yet.</p>
        )}
      </div>
    </div>
  )
}
