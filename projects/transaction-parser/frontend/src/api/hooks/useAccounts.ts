import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Account } from '../types'

export function useAccounts() {
  return useQuery({
    queryKey: queryKeys.accounts,
    queryFn: () => api.get<Account[]>('/accounts'),
  })
}
