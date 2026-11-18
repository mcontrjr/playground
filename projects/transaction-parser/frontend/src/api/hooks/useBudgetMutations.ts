import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type {
  BudgetExpense,
  BudgetExpenseCreate,
  BudgetExpenseDeleteResult,
  BudgetExpenseUpdate,
} from '../types'

function useInvalidateBudget() {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: queryKeys.budgetAll })
}

export function useCreateBudgetExpense(month: string) {
  const invalidate = useInvalidateBudget()
  return useMutation({
    mutationFn: (body: BudgetExpenseCreate) =>
      api.post<BudgetExpense>(`/budget?month=${month}`, body),
    onSuccess: invalidate,
  })
}

export function usePatchBudgetExpense(month: string) {
  const invalidate = useInvalidateBudget()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: BudgetExpenseUpdate }) =>
      api.patch<BudgetExpense>(`/budget/${id}?month=${month}`, patch),
    onSuccess: invalidate,
  })
}

export function useDeleteBudgetExpense() {
  const invalidate = useInvalidateBudget()
  return useMutation({
    mutationFn: (id: number) => api.delete<BudgetExpenseDeleteResult>(`/budget/${id}`),
    onSuccess: invalidate,
  })
}
