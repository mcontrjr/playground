import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Transaction, TransactionPatch } from '../types'

export function usePatchTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: TransactionPatch }) =>
      api.patch<Transaction>(`/transactions/${id}`, patch),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.transactionsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.analyticsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories })
    },
  })
}
