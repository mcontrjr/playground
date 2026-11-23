import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type {
  ClashDismissRequest,
  ClashDismissal,
  ClashDismissalListResponse,
  ClashListResponse,
  ImpactPreviewResponse,
  RecategorizeAllRequest,
  RecategorizeAllResponse,
  ClashResolveRequest,
  ClashResolveResponse,
  ReprioritizeRequest,
  ReprioritizeResponse,
} from '../types'
import { useInvalidateEverything } from './useCategoryMutations'

/** Rows claimed by more than one category — i.e. where priority chose
 * for the user. Settled (manual/bulk) rows are excluded by default. */
export function useClashes(includeSettled = false) {
  return useQuery({
    queryKey: queryKeys.clashes(includeSettled),
    queryFn: () =>
      api.get<ClashListResponse>(
        `/categories/clashes?include_settled=${includeSettled}`,
      ),
  })
}

/** Settle a clash with the user's choice. Writes category_source='manual',
 * which is permanently sticky against every later rules pass. */
export function useResolveClash() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: ClashResolveRequest) =>
      api.post<ClashResolveResponse>('/categories/clashes/resolve', body),
    onSuccess: invalidate,
  })
}

/** Reorder category priority. Always preview with dry_run first — priority
 * is global, so a reorder can move rows unrelated to the one that
 * motivated it. */
export function useReprioritize() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: ReprioritizeRequest) =>
      api.post<ReprioritizeResponse>('/categories/reprioritize', body),
    onSuccess: (_data, variables) => {
      // A dry run changes nothing; don't churn every cached query.
      if (!variables.dry_run) invalidate()
    },
  })
}

/** Clashes a not-yet-added keyword would create. Used to warn inside the
 * add-keyword flow that priority, not the user, would pick the winner. */
export function usePreviewKeywordClashes() {
  return useMutation({
    mutationFn: (body: { category_id: number; keyword: string }) =>
      api.post<ClashListResponse>('/categories/clashes/preview-keyword', {
        action: 'add_keyword',
        ...body,
      }),
  })
}

/** Where a category's transactions would land if it were deleted and the
 * remaining rules re-run. Read-only; writes nothing. */
export function useDeleteCategoryPreview(categoryId: number | null) {
  return useQuery({
    queryKey: ['categories', 'delete-preview', categoryId],
    queryFn: () =>
      api.get<ImpactPreviewResponse>(`/categories/${categoryId}/delete-preview`),
    enabled: categoryId !== null,
  })
}

/** Re-run the current rules over every existing transaction. Categorization
 * otherwise happens only at ingest, so rules edited afterwards never reach
 * rows already in the database — this is the catch-up pass. Always preview
 * with dry_run first. */
export function useRecategorizeAll() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: RecategorizeAllRequest) =>
      api.post<RecategorizeAllResponse>('/transactions/recategorize-all', body),
    onSuccess: (_data, variables) => {
      if (!variables.dry_run) invalidate()
    },
  })
}

/** Conflicts the user judged correct as-is, and how many rows each hides. */
export function useClashDismissals() {
  return useQuery({
    queryKey: ['categories', 'clash-dismissals'],
    queryFn: () => api.get<ClashDismissalListResponse>('/categories/clashes/dismissals'),
  })
}

/** Stop listing a conflict without touching the transaction. Omit
 * transaction_id to dismiss the pairing itself (covers future imports). */
export function useDismissClash() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: ClashDismissRequest) =>
      api.post<ClashDismissal>('/categories/clashes/dismiss', body),
    onSuccess: invalidate,
  })
}

/** Return a dismissed conflict to the review queue. */
export function useUndismissClash() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/categories/clashes/dismissals/${id}`),
    onSuccess: invalidate,
  })
}
