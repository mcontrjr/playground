import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '../client'
import { queryKeys } from '../queryKeys'
import type { MonthOption, TransactionFacets, TransactionFilters, TransactionListResponse } from '../types'

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
          exclude_category_ids: filters.exclude_category_ids,
          q: filters.q,
          recurring_only: filters.recurring_only,
          include_excluded: filters.include_excluded,
          outflows_only: filters.outflows_only,
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

/** Which account/category/month chips currently have at least one
 * matching transaction — each dimension computed against every *other*
 * active filter (see /transactions/facets). The FilterBar uses this to
 * dim chips that would zero out the result set, without making a
 * chip dim just because it's the one currently selected. `q`,
 * `recurring_only`, and `include_excluded` are passed through since
 * they're not a dimension being faceted themselves; `sort`/`order`/
 * `limit`/`offset` are irrelevant here and omitted. */
export function useTransactionFacets(filters: TransactionFilters) {
  return useQuery({
    queryKey: queryKeys.transactionFacets(filters),
    queryFn: () =>
      api.get<TransactionFacets>(
        `/transactions/facets${buildQuery({
          date_from: filters.date_from,
          date_to: filters.date_to,
          account_ids: filters.account_ids,
          category_ids: filters.category_ids,
          exclude_category_ids: filters.exclude_category_ids,
          q: filters.q,
          recurring_only: filters.recurring_only,
          include_excluded: filters.include_excluded,
          outflows_only: filters.outflows_only,
        })}`,
      ),
    placeholderData: keepPreviousData,
  })
}
