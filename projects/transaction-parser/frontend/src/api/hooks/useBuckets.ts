import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Bucket } from '../types'

export function useBuckets() {
  return useQuery({
    queryKey: queryKeys.buckets,
    queryFn: () => api.get<Bucket[]>('/buckets'),
  })
}
