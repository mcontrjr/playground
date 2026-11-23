import type { TransactionFilters } from './types'

/** Centralized query-key factory so invalidation stays consistent. */
export const queryKeys = {
  transactions: (filters: TransactionFilters) => ['transactions', filters] as const,
  transactionsAll: ['transactions'] as const,
  months: ['transactions', 'months'] as const,
  transactionFacets: (filters: TransactionFilters) => ['transactions', 'facets', filters] as const,
  accounts: ['accounts'] as const,
  categories: ['categories'] as const,
  failures: (resolved?: boolean) => ['failures', resolved] as const,
  failuresAll: ['failures'] as const,
  batches: ['batches'] as const,
  analyticsAll: ['analytics'] as const,
  analyticsSummary: (params: unknown) => ['analytics', 'summary', params] as const,
  analyticsTimeseries: (params: unknown) => ['analytics', 'timeseries', params] as const,
  analyticsMonthlyDaily: (params: unknown) => ['analytics', 'monthly-daily', params] as const,
  analyticsDistribution: (params: unknown) => ['analytics', 'distribution', params] as const,
  preference: (key: string) => ['preferences', key] as const,
  buckets: ['buckets'] as const,
  audit: (params: unknown) => ['audit', params] as const,
  auditAll: ['audit'] as const,
  budgetSummary: (month: string) => ['budget', 'summary', month] as const,
  budgetAll: ['budget'] as const,
  clashes: (includeSettled: boolean) => ['categories', 'clashes', includeSettled] as const,
  clashesAll: ['categories', 'clashes'] as const,
  workspaceBootstrap: (slug: string) => ['workspace', slug, 'bootstrap'] as const,
  workspaceAvailability: (slug: string) => ['workspace', 'availability', slug] as const,
}
