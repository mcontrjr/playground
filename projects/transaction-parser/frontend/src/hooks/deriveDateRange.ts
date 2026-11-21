import type { DateRange } from '../components/DateRangePicker/DateRangePicker'
import type { MonthOption } from '../api/types'

/** Resolves month chips + a custom date range (mutually exclusive at
 * the filter-bar level — picking one clears the other) into concrete
 * date_from/date_to bounds. A custom range takes priority verbatim if
 * both are ever populated. Shared by Records and the three analytics
 * pages (Overview, Time Series, Distribution), which all use the same
 * month-chips-or-range control alongside their own MonthSwiper
 * fallback. */
export function deriveDateRange(
  filters: { monthKeys: string[]; dateRange?: DateRange },
  options: MonthOption[],
): { date_from?: string; date_to?: string } {
  if (filters.dateRange) return { date_from: filters.dateRange.from, date_to: filters.dateRange.to }
  if (filters.monthKeys.length === 0) return {}
  const selected = options.filter((option) => filters.monthKeys.includes(option.key))
  if (selected.length === 0) return {}
  const from = selected.reduce((min, o) => (o.from < min ? o.from : min), selected[0]!.from)
  const to = selected.reduce((max, o) => (o.to > max ? o.to : max), selected[0]!.to)
  return { date_from: from, date_to: to }
}
