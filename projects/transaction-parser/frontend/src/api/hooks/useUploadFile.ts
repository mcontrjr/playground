import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError, api } from '../client'
import { queryKeys } from '../queryKeys'
import type { AmbiguousInstitutionDetail, BatchDetail } from '../types'

export class AmbiguousInstitutionApiError extends ApiError {
  readonly candidates: string[]

  constructor(apiError: ApiError) {
    super(apiError.status, apiError.detail)
    this.name = 'AmbiguousInstitutionApiError'
    const detail = apiError.detail as AmbiguousInstitutionDetail
    this.candidates = detail.candidates
  }

  static isAmbiguous(error: unknown): error is ApiError {
    return (
      error instanceof ApiError &&
      error.status === 409 &&
      error.code === 'AMBIGUOUS_INSTITUTION'
    )
  }
}

export interface UploadFileArgs {
  file: File
  institution?: string
}

export function useUploadFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ file, institution }: UploadFileArgs) => {
      const form = new FormData()
      form.append('file', file)
      if (institution) form.append('institution', institution)

      try {
        return await api.postForm<BatchDetail>('/uploads', form)
      } catch (error) {
        if (AmbiguousInstitutionApiError.isAmbiguous(error)) {
          throw new AmbiguousInstitutionApiError(error)
        }
        throw error
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches })
      void queryClient.invalidateQueries({ queryKey: queryKeys.transactionsAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.accounts })
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories })
      void queryClient.invalidateQueries({ queryKey: queryKeys.failuresAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.analyticsAll })
    },
  })
}
