import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Category } from '../types'

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => api.get<Category[]>('/categories'),
  })
}
