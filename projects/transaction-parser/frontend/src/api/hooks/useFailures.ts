import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, buildQuery } from '../client'
import { queryKeys } from '../queryKeys'
import type { ParseFailure, ParseFailurePatch } from '../types'

export function useFailures(resolved?: boolean) {
  return useQuery({
    queryKey: queryKeys.failures(resolved),
    queryFn: () =>
      api.get<ParseFailure[]>(`/failures${buildQuery({ resolved })}`),
  })
}

export function usePatchFailure() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: ParseFailurePatch }) =>
      api.patch<ParseFailure>(`/failures/${id}`, patch),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.failuresAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches })
    },
  })
}
