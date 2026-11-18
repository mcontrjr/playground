import { useMutation } from '@tanstack/react-query'
import { api } from '../client'
import type { Bucket, BucketCreate, BucketDeleteResult, BucketUpdate } from '../types'
import { useInvalidateEverything } from './useCategoryMutations'

/** Bucket mutations reuse categories' `useInvalidateEverything` —
 * renaming/deleting a bucket changes category `group` labels and can
 * reassign categories, which reshapes the same surfaces a category
 * mutation does, plus it always produces an audit event. */
export function useCreateBucket() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: (body: BucketCreate) => api.post<Bucket>('/buckets', body),
    onSuccess: invalidate,
  })
}

export function usePatchBucket() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: BucketUpdate }) =>
      api.patch<Bucket>(`/buckets/${id}`, patch),
    onSuccess: invalidate,
  })
}

export function useDeleteBucket() {
  const invalidate = useInvalidateEverything()
  return useMutation({
    mutationFn: ({ id, reassignToBucketId }: { id: number; reassignToBucketId?: number }) =>
      api.delete<BucketDeleteResult>(
        `/buckets/${id}${reassignToBucketId != null ? `?reassign_to_bucket_id=${reassignToBucketId}` : ''}`,
      ),
    onSuccess: invalidate,
  })
}
