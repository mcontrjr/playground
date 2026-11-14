import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Account, AccountPatch } from '../types'

/** Renaming an account changes a label every filter chip and every
 * transaction row reads (account_name is joined server-side), so this
 * invalidates transactions/analytics alongside accounts itself —
 * mirrors the invalidation breadth category mutations already use. */
export function usePatchAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: AccountPatch }) =>
      api.patch<Account>(`/accounts/${id}`, patch),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.accounts })
      void queryClient.invalidateQueries({ queryKey: queryKeys.transactionsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.analyticsAll })
    },
  })
}
