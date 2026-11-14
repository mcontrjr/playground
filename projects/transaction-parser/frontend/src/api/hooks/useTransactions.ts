import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '../client'
import { queryKeys } from '../queryKeys'
import type { MonthOption, TransactionFilters, TransactionListResponse } from '../types'

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: queryKeys.transactions(filters),
    queryFn: () =>
      api.get<TransactionListResponse>(
        `/transactions${buildQuery({
          date_from: filters.date_from,
          date_to: filters.date_to,
          account_ids: filters.account_ids,
          category_ids: filters.category_ids,
          q: filters.q,
          recurring_only: filters.recurring_only,
          include_excluded: filters.include_excluded,
          sort: filters.sort,
          order: filters.order,
          limit: filters.limit,
          offset: filters.offset,
        })}`,
      ),
    placeholderData: keepPreviousData,
  })
}

/** Months that actually have at least one transaction, computed in SQL
 * (see /transactions/months) — replaces deriving a min..max date range
 * client-side, which wrongly implied every month in that span has data. */
export function useMonths() {
  return useQuery({
    queryKey: queryKeys.months,
    queryFn: () => api.get<MonthOption[]>('/transactions/months'),
    staleTime: 60_000,
  })
}
