import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '../client'
import { queryKeys } from '../queryKeys'
import type { AuditPage } from '../types'

export interface AuditEventsParams {
  limit: number
  offset: number
}

/** Offset-paginated audit trail — `keepPreviousData` so "Load more"
 * (bumping `offset`/`limit`) doesn't flash the list to a loading
 * state between pages. */
export function useAuditEvents({ limit, offset }: AuditEventsParams) {
  return useQuery({
    queryKey: queryKeys.audit({ limit, offset }),
    queryFn: () => api.get<AuditPage>(`/audit${buildQuery({ limit, offset })}`),
    placeholderData: keepPreviousData,
  })
}
