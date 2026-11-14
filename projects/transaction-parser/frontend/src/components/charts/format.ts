const CURRENCY = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const CURRENCY_PRECISE = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

/** Formats a decimal string (as returned by the API) as whole-dollar
 * currency, e.g. "1234.56" -> "$1,235". */
export function formatCurrency(value: string | number): string {
  const n = typeof value === 'string' ? Number(value) : value
  return CURRENCY.format(n)
}

/** Formats with cents, for tooltips and precise contexts. */
export function formatCurrencyPrecise(value: string | number): string {
  const n = typeof value === 'string' ? Number(value) : value
  return CURRENCY_PRECISE.format(n)
}

export function formatPercent(fraction: number): string {
  if (!Number.isFinite(fraction)) return '0%'
  return `${(fraction * 100).toFixed(fraction < 0.1 ? 1 : 0)}%`
}

/** "2026-09" -> "Sep 2026" */
export function formatMonthPeriod(period: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(period)
  if (!match) return period
  const [, year, month] = match
  const date = new Date(Number(year), Number(month) - 1, 1)
  return new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric' }).format(date)
}

/** "2026-W37" -> "Wk 37" */
export function formatWeekPeriod(period: string): string {
  const match = /^(\d{4})-W(\d{2})$/.exec(period)
  if (!match) return period
  return `Wk ${match[2]}`
}

export function formatPeriod(period: string, granularity: 'month' | 'week'): string {
  return granularity === 'month' ? formatMonthPeriod(period) : formatWeekPeriod(period)
}
