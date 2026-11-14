import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type {
  Category,
  CategoryCreate,
  CategoryDeleteResponse,
  CategoryKeywordCreate,
  CategoryKeywordCreateResponse,
  CategoryKeywordDeleteResponse,
  CategoryPatch,
  CategoryPatchResponse,
  ImpactPreviewRequest,
  ImpactPreviewResponse,
} from '../types'

/** Mutations that change categories/keywords invalidate categories,
 * transactions, and analytics everywhere — a keyword or rename can
 * reshape every page that reads category assignments. */
function useInvalidateEverything() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.categories })
    void queryClient.invalidateQueries({ queryKey: queryKeys.transactionsAll })
    void queryClient.invalidateQueries({ queryKey: queryKeys.analyticsAll })
  }
}

export function useCreateCategory() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: CategoryCreate) => api.post<Category>('/categories', body),
    onSuccess: invalidate,
  })
}

export function usePatchCategory() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: CategoryPatch }) =>
      api.patch<CategoryPatchResponse>(`/categories/${id}`, patch),
    onSuccess: invalidate,
  })
}

export function useDeleteCategory() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (id: number) => api.delete<CategoryDeleteResponse>(`/categories/${id}`),
    onSuccess: invalidate,
  })
}

export function useImpactPreview() {
  return useMutation({
    mutationFn: (body: ImpactPreviewRequest) =>
      api.post<ImpactPreviewResponse>('/categories/impact-preview', body),
  })
}

export function useAddKeyword() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: ({ categoryId, body }: { categoryId: number; body: CategoryKeywordCreate }) =>
      api.post<CategoryKeywordCreateResponse>(`/categories/${categoryId}/keywords`, body),
    onSuccess: invalidate,
  })
}

export function useDeleteKeyword() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: ({
      categoryId,
      keywordId,
      reapply,
    }: {
      categoryId: number
      keywordId: number
      reapply: boolean
    }) =>
      api.delete<CategoryKeywordDeleteResponse>(
        `/categories/${categoryId}/keywords/${keywordId}?reapply=${reapply}`,
      ),
    onSuccess: invalidate,
  })
}
