import { useState } from 'react'
import { useMonths } from '../api/hooks/useTransactions'
import type { MonthOption } from '../api/types'

export interface MonthScope {
  /** Null = "All" (the default scope on every page that uses this
   * hook); otherwise the active month's display label. */
  label: string
  isAll: boolean
  canGoNewer: boolean
  canGoOlder: boolean
  goNewer: () => void
  goOlder: () => void
  /** Undefined in "All" mode — callers pass these straight through to
   * `AnalyticsFilters`/`TransactionFilters`, where undefined means
   * "no date bound". */
  dateFrom: string | undefined
  dateTo: string | undefined
  /** The active `MonthOption`, or undefined in "All" mode / before
   * `useMonths()` has resolved. */
  month: MonthOption | undefined
}

/** Wraps `useMonths()` with a single swipeable position: "All" (the
 * default, index `null`) → newest month (index 0) → older months
 * (ascending index). Every page that swipes between an all-time view
 * and per-month views (Overview, Time Series, Distribution) shares
 * this instead of re-deriving the index arithmetic three times. */
export function useMonthScope(): MonthScope {
  const { data: months } = useMonths()
  const [monthIndex, setMonthIndex] = useState<number | null>(null)

  const isAll = monthIndex === null
  const activeMonth = monthIndex === null ? undefined : months?.[monthIndex]

  const canGoNewer = monthIndex !== null
  const canGoOlder = isAll
    ? !!months && months.length > 0
    : !!months && monthIndex! < months.length - 1

  const goNewer = () => {
    setMonthIndex((current) => {
      if (current === null) return current
      if (current === 0) return null
      return current - 1
    })
  }

  const goOlder = () => {
    setMonthIndex((current) => {
      if (current === null) return 0
      if (!months) return current
      return Math.min(months.length - 1, current + 1)
    })
  }

  const label = isAll ? 'All records' : activeMonth?.label ?? 'Loading…'

  return {
    label,
    isAll,
    canGoNewer,
    canGoOlder,
    goNewer,
    goOlder,
    dateFrom: activeMonth?.from,
    dateTo: activeMonth?.to,
    month: activeMonth,
  }
}
