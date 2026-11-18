import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { BulkRecategorizeRequest, BulkRecategorizeResponse } from '../types'

export function useBulkRecategorize() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: BulkRecategorizeRequest) =>
      api.post<BulkRecategorizeResponse>('/transactions/bulk-recategorize', body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.transactionsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.analyticsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories })
      void queryClient.invalidateQueries({ queryKey: queryKeys.auditAll })
    },
  })
}
