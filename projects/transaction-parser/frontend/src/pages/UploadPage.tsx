import { useMemo, useState } from 'react'
import { ApiError } from '../api/client'
import { useBatches } from '../api/hooks/useBatches'
import { useFailures } from '../api/hooks/useFailures'
import { AmbiguousInstitutionApiError, useUploadFile } from '../api/hooks/useUploadFile'
import { useWorkspaceBootstrap } from '../api/hooks/useWorkspaceBootstrap'
import type { BatchDetail, ParseFailure } from '../api/types'
import { BatchList } from '../components/BatchList/BatchList'
import { FailuresList } from '../components/FailuresList/FailuresList'
import { InstitutionPickerDialog } from '../components/InstitutionPickerDialog/InstitutionPickerDialog'
import { LoadingOverlay } from '../components/LogoSpinner/LogoSpinner'
import { UploadDropzone } from '../components/UploadDropzone/UploadDropzone'
import styles from './UploadPage.module.css'

type QueueItemStatus = 'pending' | 'uploading' | 'done' | 'error'

interface QueueItem {
  id: string
  file: File
  status: QueueItemStatus
  errorMessage?: string
}

const STATUS_LABEL: Record<QueueItemStatus, string> = {
  pending: 'Queued',
  uploading: 'Uploading…',
  done: 'Done',
  error: 'Failed',
}

const STATUS_CLASS: Record<QueueItemStatus, string> = {
  pending: styles.statusPending,
  uploading: styles.statusUploading,
  done: styles.statusDone,
  error: styles.statusError,
}

function makeQueueId(file: File, index: number): string {
  return `${file.name}-${file.size}-${index}-${Date.now()}`
}

export function UploadPage() {
  const uploadFile = useUploadFile()
  const { data: bootstrap, refetch: refetchBootstrap } = useWorkspaceBootstrap()
  const { data: batches } = useBatches()
  const { data: unresolvedFailures } = useFailures(false)
  // Unfiltered, so a failure resolved from the in-session results panel
  // (below) is reflected without requiring that panel to hold its own
  // query state — `results` is a local snapshot of each upload's
  // response and would otherwise never learn that resolution happened.
  const { data: allFailures } = useFailures()
  const liveFailuresById = useMemo(() => {
    const map = new Map<number, ParseFailure>()
    for (const failure of allFailures ?? []) map.set(failure.id, failure)
    return map
  }, [allFailures])

  const [queue, setQueue] = useState<QueueItem[]>([])
  const [results, setResults] = useState<BatchDetail[]>([])
  const [pendingAmbiguity, setPendingAmbiguity] = useState<{
    item: QueueItem
    rest: QueueItem[]
    candidates: string[]
  } | null>(null)
  /** True while the workspace's first import is being absorbed. */
  const [unlocking, setUnlocking] = useState(false)

  const hadRecordsBefore = bootstrap?.has_transactions ?? false

  /** Uploads one file; on success, records the result and reports it. On
   * ambiguity, surfaces the candidates for the dialog instead of throwing. */
  const uploadOne = async (
    item: QueueItem,
    institution?: string,
  ): Promise<{ ambiguous: string[] } | null> => {
    setQueue((current) =>
      current.map((q) => (q.id === item.id ? { ...q, status: 'uploading' } : q)),
    )
    try {
      const result = await uploadFile.mutateAsync({ file: item.file, institution })
      setQueue((current) =>
        current.map((q) => (q.id === item.id ? { ...q, status: 'done' } : q)),
      )
      setResults((current) => [result, ...current])
      return null
    } catch (error) {
      if (AmbiguousInstitutionApiError.isAmbiguous(error)) {
        return { ambiguous: (error as AmbiguousInstitutionApiError).candidates }
      }
      const message = error instanceof ApiError ? error.message : 'Upload failed.'
      setQueue((current) =>
        current.map((q) =>
          q.id === item.id ? { ...q, status: 'error', errorMessage: message } : q,
        ),
      )
      return null
    }
  }

  /** Re-read the workspace so `has_transactions` (and therefore the
   * sidebar) reflects what was just imported. On the very first import
   * this is the moment the rest of the app unlocks, so it gets the
   * spinning logo rather than a silent nav change. */
  const absorbImport = async () => {
    if (hadRecordsBefore) {
      void refetchBootstrap()
      return
    }
    setUnlocking(true)
    try {
      await refetchBootstrap()
    } finally {
      setUnlocking(false)
    }
  }

  const processQueue = async (items: QueueItem[]) => {
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i]!
      const outcome = await uploadOne(item)
      if (outcome) {
        setPendingAmbiguity({ item, rest: items.slice(i + 1), candidates: outcome.ambiguous })
        return
      }
    }
    await absorbImport()
  }

  const handleFilesSelected = (files: File[]) => {
    const newItems: QueueItem[] = files.map((file, index) => ({
      id: makeQueueId(file, index),
      file,
      status: 'pending',
    }))
    setQueue((current) => [...current, ...newItems])
    void processQueue(newItems)
  }

  const handleAmbiguityResolved = async (institution: string) => {
    if (!pendingAmbiguity) return
    const { item, rest } = pendingAmbiguity
    setPendingAmbiguity(null)
    await uploadOne(item, institution)
    void processQueue(rest)
  }

  const handleAmbiguityCancelled = () => {
    if (!pendingAmbiguity) return
    const { item, rest } = pendingAmbiguity
    setPendingAmbiguity(null)
    setQueue((current) =>
      current.map((q) =>
        q.id === item.id ? { ...q, status: 'error', errorMessage: 'Cancelled.' } : q,
      ),
    )
    void processQueue(rest)
  }

  // The first import unlocks the rest of the app, so it takes over the
  // page with the same spinning logo the splash screen uses.
  if (unlocking) {
    return (
      <div className={styles.page}>
        <LoadingOverlay message="Importing your records" />
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Upload</h1>

      <UploadDropzone onFilesSelected={handleFilesSelected} disabled={!!pendingAmbiguity} />

      {queue.length > 0 && (
        <section className={styles.section}>
          <span className={styles.sectionHeading}>This session</span>
          <ul className={styles.queue}>
            {queue.map((item) => (
              <li key={item.id} className={styles.queueItem}>
                <span className={styles.queueFilename}>
                  {item.file.name}
                  {item.errorMessage ? ` — ${item.errorMessage}` : ''}
                </span>
                <span className={`${styles.queueStatus} ${STATUS_CLASS[item.status]}`}>
                  {STATUS_LABEL[item.status]}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {results.length > 0 && (
        <section className={styles.section}>
          <span className={styles.sectionHeading}>Results</span>
          {results.map((batch) => (
            <div
              key={`${batch.id}-${batch.created_at}`}
              className={styles.resultPanel}
              data-testid="upload-result"
            >
              <div className={styles.resultHeader}>
                <span className={styles.resultFilename}>{batch.filename}</span>
              </div>
              <div className={styles.resultStats}>
                <div className={styles.stat}>
                  <span className={styles.statValue} data-testid="upload-result-inserted">
                    {batch.counts.inserted}
                  </span>
                  <span className={styles.statLabel}>Inserted</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statValue} data-testid="upload-result-duplicates">
                    {batch.counts.duplicates}
                  </span>
                  <span className={styles.statLabel}>Duplicates</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statValue} data-testid="upload-result-failures">
                    {batch.counts.failures}
                  </span>
                  <span className={styles.statLabel}>Failures</span>
                </div>
              </div>
              {batch.failures.length > 0 && (
                <>
                  <span className={styles.failuresHeading}>Parse failures</span>
                  <FailuresList
                    failures={batch.failures.map((f) => liveFailuresById.get(f.id) ?? f)}
                  />
                </>
              )}
            </div>
          ))}
        </section>
      )}

      {unresolvedFailures && unresolvedFailures.length > 0 && (
        <section className={styles.section}>
          <span className={styles.sectionHeading}>
            Unresolved failures from previous uploads ({unresolvedFailures.length})
          </span>
          <FailuresList failures={unresolvedFailures} />
        </section>
      )}

      <section className={styles.section}>
        <span className={styles.sectionHeading}>Recent batches</span>
        <BatchList batches={batches ?? []} />
      </section>

      {pendingAmbiguity && (
        <InstitutionPickerDialog
          filename={pendingAmbiguity.item.file.name}
          candidates={pendingAmbiguity.candidates}
          onConfirm={(institution) => void handleAmbiguityResolved(institution)}
          onCancel={handleAmbiguityCancelled}
        />
      )}
    </div>
  )
}
