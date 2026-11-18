import { useMemo } from 'react'
import { useAnalyticsDistribution, useAnalyticsSummary, useAnalyticsTimeseries } from '../api/hooks/useAnalytics'
import { useMonthScope } from '../hooks/useMonthScope'
import { formatCurrency, formatMonthPeriod } from '../components/charts/format'
import { KpiTile } from '../components/charts/KpiTile'
import { MiniBarChart } from '../components/charts/MiniBarChart'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import styles from './OverviewPage.module.css'

const TOP_N = 5

function formatDateRange(from: string | null, to: string | null): string {
  if (!from || !to) return 'No transactions in range yet.'
  const formatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${formatter.format(new Date(`${from}T00:00:00`))} – ${formatter.format(
    new Date(`${to}T00:00:00`),
  )}`
}

export function OverviewPage() {
  const scope = useMonthScope()
  const analyticsFilters = { date_from: scope.dateFrom, date_to: scope.dateTo }

  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(analyticsFilters)
  const { data: distribution } = useAnalyticsDistribution(analyticsFilters)
  const { data: timeseries } = useAnalyticsTimeseries('month', analyticsFilters)

  const topCategories = useMemo(() => (distribution?.entries ?? []).slice(0, TOP_N), [distribution])

  const monthlySpend = useMemo(() => {
    if (!timeseries) return []
    return timeseries.periods.map((period, i) => {
      const total = timeseries.series.reduce((sum, s) => sum + Math.abs(Number(s.values[i]?.value ?? 0)), 0)
      return { label: formatMonthPeriod(period), value: total }
    })
  }, [timeseries])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Overview</h1>
        <p className={styles.dateRange}>
          {summaryLoading
            ? 'Loading…'
            : formatDateRange(summary?.date_from ?? null, summary?.date_to ?? null)}
        </p>
      </header>

      <MonthSwiper
        label={scope.label}
        canGoNewer={scope.canGoNewer}
        canGoOlder={scope.canGoOlder}
        badge={scope.isAll ? 'Entire history' : 'Month view'}
        onNewer={scope.goNewer}
        onOlder={scope.goOlder}
      />

      <div className={styles.kpiRow}>
        <KpiTile label="Total spent" value={summary ? formatCurrency(summary.total_spent) : '—'} />
        <KpiTile
          label="Money in"
          value={summary ? formatCurrency(summary.total_in) : '—'}
          tone="positive"
        />
        <KpiTile
          label="Net"
          value={summary ? formatCurrency(summary.net) : '—'}
          tone={summary && Number(summary.net) < 0 ? 'negative' : 'positive'}
        />
        <KpiTile
          label="Transactions"
          value={summary ? summary.transaction_count.toLocaleString('en-US') : '—'}
          sub={
            summary?.largest_transaction
              ? `Largest: ${formatCurrency(summary.largest_transaction)}`
              : undefined
          }
        />
      </div>

      <div className={styles.lowerRow}>
        <section className={styles.panel}>
          <h2 className={styles.panelHeading}>Monthly spend</h2>
          {monthlySpend.length > 0 ? (
            <MiniBarChart data={monthlySpend} />
          ) : (
            <p className={styles.empty}>Not enough data yet.</p>
          )}
        </section>

        <section className={styles.panel}>
          <h2 className={styles.panelHeading}>Top categories</h2>
          {topCategories.length > 0 ? (
            <div className={styles.topCategories}>
              {topCategories.map((entry, i) => (
                <div className={styles.topRow} key={entry.category_id}>
                  <span className={styles.topRank}>{i + 1}</span>
                  <span className={styles.topName}>{entry.name}</span>
                  <span className={styles.topAmount}>{formatCurrency(entry.amount)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>No categorized spend yet.</p>
          )}
        </section>
      </div>
    </div>
  )
}
