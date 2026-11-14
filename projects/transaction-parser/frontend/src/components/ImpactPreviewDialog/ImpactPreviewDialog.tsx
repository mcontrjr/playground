import { useEffect, useState } from 'react'
import { ApiError } from '../../api/client'
import { useImpactPreview } from '../../api/hooks/useCategoryMutations'
import type { ImpactPreviewAction } from '../../api/types'
import { Modal } from '../Modal/Modal'
import styles from './ImpactPreviewDialog.module.css'

interface ImpactPreviewDialogProps {
  action: ImpactPreviewAction
  categoryId: number
  categoryName: string
  keyword: string
  /** Called when the user confirms. Receives whether "apply to
   * existing" / "reapply" was checked — the caller performs the real
   * mutation (add-keyword or delete-keyword) with that flag. */
  onConfirm: (applyToExisting: boolean) => void
  onCancel: () => void
  isCommitting?: boolean
  commitError?: string | null
}

/** The workflow centerpiece: ALWAYS run a dry-run preview before a
 * keyword add/remove is committed. Shows the affected count, a
 * from→to breakdown, and a capped sample of the actual rows that
 * would move — then lets the user opt in to applying it to existing
 * transactions before confirming. */
export function ImpactPreviewDialog({
  action,
  categoryId,
  categoryName,
  keyword,
  onConfirm,
  onCancel,
  isCommitting,
  commitError,
}: ImpactPreviewDialogProps) {
  const preview = useImpactPreview()
  const [applyToExisting, setApplyToExisting] = useState(action === 'add_keyword')

  useEffect(() => {
    preview.mutate({ action, category_id: categoryId, keyword })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [action, categoryId, keyword])

  const verb = action === 'add_keyword' ? 'add' : 'remove'
  const applyLabel =
    action === 'add_keyword'
      ? 'Apply to existing transactions now'
      : 'Re-categorize affected transactions now'

  return (
    <Modal
      title={`${verb === 'add' ? 'Add' : 'Remove'} keyword`}
      onClose={onCancel}
      wide
      ariaLabel="Keyword impact preview"
    >
      <p className={styles.intro}>
        {verb === 'add' ? (
          <>
            Adding <span className={styles.keyword}>"{keyword}"</span> to{' '}
            <span className={styles.keyword}>{categoryName}</span> would re-categorize these
            transactions if applied.
          </>
        ) : (
          <>
            Removing <span className={styles.keyword}>"{keyword}"</span> from{' '}
            <span className={styles.keyword}>{categoryName}</span> would re-categorize these
            transactions if re-applied.
          </>
        )}
      </p>

      {preview.isPending && <p className={styles.loading}>Checking impact…</p>}

      {preview.isError && (
        <p className={styles.errorBanner}>
          {preview.error instanceof ApiError ? preview.error.message : 'Could not preview impact.'}
        </p>
      )}

      {preview.data && (
        <>
          <div className={styles.affectedCount} data-testid="impact-affected-count" data-count={preview.data.affected_count}>
            <span className={styles.affectedNumber}>{preview.data.affected_count}</span>
            <span className={styles.affectedLabel}>
              transaction{preview.data.affected_count === 1 ? '' : 's'} affected
            </span>
          </div>

          {preview.data.affected_count === 0 ? (
            <p className={styles.noChange}>No existing transactions would change category.</p>
          ) : (
            <>
              {preview.data.breakdown.length > 0 && (
                <>
                  <span className={styles.sectionLabel}>Breakdown</span>
                  <table className={styles.breakdownTable} data-testid="impact-breakdown-table">
                    <thead>
                      <tr>
                        <th>From</th>
                        <th />
                        <th>To</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.data.breakdown.map((entry) => (
                        <tr key={`${entry.from_category_id}-${entry.to_category_id}`}>
                          <td>{entry.from_category}</td>
                          <td className={styles.arrow}>&rarr;</td>
                          <td>{entry.to_category}</td>
                          <td className={styles.countCell}>{entry.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}

              {preview.data.sample.length > 0 && (
                <>
                  <span className={styles.sectionLabel}>Sample transactions</span>
                  <div className={styles.sampleList}>
                    {preview.data.sample.map((txn) => (
                      <div className={styles.sampleRow} key={txn.id}>
                        <span className={styles.sampleDescription}>{txn.description}</span>
                        <span className={styles.sampleCategoryChange}>
                          {txn.current_category_name ?? 'Uncategorized'} &rarr;{' '}
                          {txn.new_category_name ?? 'Uncategorized'}
                        </span>
                      </div>
                    ))}
                    {preview.data.affected_count > preview.data.sample.length && (
                      <div className={styles.sampleMore}>
                        +{preview.data.affected_count - preview.data.sample.length} more not shown
                      </div>
                    )}
                  </div>
                </>
              )}

              <label className={styles.applyRow}>
                <input
                  type="checkbox"
                  className={styles.applyCheckbox}
                  checked={applyToExisting}
                  onChange={(event) => setApplyToExisting(event.target.checked)}
                />
                <span className={styles.applyText}>
                  <span className={styles.applyTextStrong}>{applyLabel}.</span>{' '}
                  {applyToExisting
                    ? `All ${preview.data.affected_count} transaction${
                        preview.data.affected_count === 1 ? '' : 's'
                      } above will move now.`
                    : 'Only new transactions will be affected; existing ones stay as they are.'}
                </span>
              </label>
            </>
          )}
        </>
      )}

      {commitError && <p className={styles.errorBanner}>{commitError}</p>}

      <div className={styles.actions}>
        <button type="button" className={styles.cancelButton} onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.confirmButton}
          disabled={!preview.data || isCommitting}
          onClick={() => onConfirm(applyToExisting)}
          data-testid="impact-preview-confirm"
        >
          {isCommitting ? 'Applying…' : verb === 'add' ? 'Add keyword' : 'Remove keyword'}
        </button>
      </div>
    </Modal>
  )
}
