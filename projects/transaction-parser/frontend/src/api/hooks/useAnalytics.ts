import { useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '../client'
import { queryKeys } from '../queryKeys'
import type {
  AnalyticsFilters,
  AnalyticsSummary,
  DistributionResponse,
  Granularity,
  MonthlyDailySeries,
  TimeseriesResponse,
} from '../types'

function analyticsQuery(filters: AnalyticsFilters): string {
  return buildQuery({
    date_from: filters.date_from,
    date_to: filters.date_to,
    account_ids: filters.account_ids,
    include_excluded: filters.include_excluded,
  })
}

export function useAnalyticsSummary(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: queryKeys.analyticsSummary(filters),
    queryFn: () => api.get<AnalyticsSummary>(`/analytics/summary${analyticsQuery(filters)}`),
  })
}

export function useAnalyticsDistribution(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: queryKeys.analyticsDistribution(filters),
    queryFn: () =>
      api.get<DistributionResponse>(`/analytics/distribution${analyticsQuery(filters)}`),
  })
}

export function useAnalyticsTimeseries(
  granularity: Granularity,
  filters: AnalyticsFilters,
) {
  return useQuery({
    queryKey: queryKeys.analyticsTimeseries({ granularity, ...filters }),
    queryFn: () =>
      api.get<TimeseriesResponse>(
        `/analytics/timeseries${buildQuery({
          granularity,
          date_from: filters.date_from,
          date_to: filters.date_to,
          account_ids: filters.account_ids,
          include_excluded: filters.include_excluded,
        })}`,
      ),
  })
}

/** One month's per-day net totals + running cumulative total — the
 * Time Series page's primary data source. `month` is any ISO date
 * within the target month (only year/month are used server-side). */
export function useAnalyticsMonthlyDaily(
  month: string,
  filters: Pick<AnalyticsFilters, 'account_ids' | 'include_excluded'>,
) {
  return useQuery({
    queryKey: queryKeys.analyticsMonthlyDaily({ month, ...filters }),
    queryFn: () =>
      api.get<MonthlyDailySeries>(
        `/analytics/monthly-daily${buildQuery({
          month,
          account_ids: filters.account_ids,
          include_excluded: filters.include_excluded,
        })}`,
      ),
  })
}
