import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { BatchSummary } from '../types'

export function useBatches(limit = 50) {
  return useQuery({
    queryKey: [...queryKeys.batches, limit],
    queryFn: () => api.get<BatchSummary[]>(`/uploads?limit=${limit}`),
  })
}
