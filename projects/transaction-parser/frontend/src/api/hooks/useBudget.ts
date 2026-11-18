import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { BudgetSummary } from '../types'

export function useBudgetSummary(month: string) {
  return useQuery({
    queryKey: queryKeys.budgetSummary(month),
    queryFn: () => api.get<BudgetSummary>(`/budget/summary?month=${month}`),
    enabled: !!month,
  })
}
