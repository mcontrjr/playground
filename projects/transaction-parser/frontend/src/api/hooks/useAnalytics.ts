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

/** `exclude_category_ids` is threaded in here rather than in the shared
 * `analyticsQuery` because /distribution is the only analytics endpoint
 * that accepts it — sending it to the others would be a silently
 * ignored param. */
export function useAnalyticsDistribution(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: queryKeys.analyticsDistribution(filters),
    queryFn: () =>
      api.get<DistributionResponse>(
        `/analytics/distribution${buildQuery({
          date_from: filters.date_from,
          date_to: filters.date_to,
          account_ids: filters.account_ids,
          include_excluded: filters.include_excluded,
          exclude_category_ids: filters.exclude_category_ids,
        })}`,
      ),
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
 * within the target month (only year/month are used server-side).
 * Pass `enabled: false` (e.g. when the page is in "All records"
 * mode and has no single month to ask about) to skip firing the
 * request entirely — otherwise an empty `month` still hits the API
 * with a blank `month` param and 422s. */
export function useAnalyticsMonthlyDaily(
  month: string,
  filters: Pick<AnalyticsFilters, 'account_ids' | 'include_excluded'>,
  options?: { enabled?: boolean },
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
    enabled: options?.enabled ?? true,
  })
}
