import { useEffect } from 'react'
import { useRecategorizeAll } from '../../api/hooks/useClashes'
import { Modal } from '../Modal/Modal'
import styles from './RecategorizeAllDialog.module.css'

interface RecategorizeAllDialogProps {
  onCancel: () => void
  onDone: (message: string) => void
}

/** Catch-up pass over every existing record.
 *
 * Categorization normally runs only at ingest, so rows keep whatever
 * category they got when first imported. Keywords added, reordered, or
 * deleted afterwards never reach them — `apply_to_existing` covers a
 * single keyword edit, but nothing covers the accumulated drift. This
 * re-runs the live rules over everything and reports the difference.
 *
 * Always previews first (the endpoint defaults to dry_run), since this
 * is the widest-reaching action in the app. Manual and bulk rows are
 * never touched. */
export function RecategorizeAllDialog({ onCancel, onDone }: RecategorizeAllDialogProps) {
  const run = useRecategorizeAll()
  const preview = run.data?.dry_run ? run.data : null

  useEffect(() => {
    run.mutate({ dry_run: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const apply = () => {
    run.mutate(
      { dry_run: false },
      {
        onSuccess: (res) => {
          onDone(
            res.affected_count > 0
              ? `Re-ran rules — ${res.affected_count} record${res.affected_count === 1 ? '' : 's'} recategorized.`
              : 'Re-ran rules — nothing needed changing.',
          )
        },
      },
    )
  }

  return (
    <Modal title="Re-run categorization rules" onClose={onCancel} ariaLabel="Re-run rules" wide>
      <p className={styles.body}>
        Records are categorized when they&apos;re imported, so rules you
        changed afterwards haven&apos;t reached the ones already here. This
        re-checks every record against the current rules.
      </p>

      {run.isPending && !preview && <p className={styles.muted}>Checking…</p>}

      {preview && (
        <>
          <div className={styles.countBox}>
            <span className={styles.bigNumber}>{preview.candidate_count}</span>
            <span className={styles.countLabel}>
              record{preview.candidate_count === 1 ? '' : 's'} would change
            </span>
          </div>

          {preview.skipped_sticky_count > 0 && (
            <p className={styles.muted}>
              {preview.skipped_sticky_count} record
              {preview.skipped_sticky_count === 1 ? '' : 's'} you set by hand are excluded and
              will not move.
            </p>
          )}

          {preview.moves.length > 0 && (
            <ul className={styles.list}>
              {preview.moves.slice(0, 12).map((m) => (
                <li key={m.transaction_id} className={styles.row}>
                  <span className={styles.desc} title={m.description}>
                    {m.description}
                  </span>
                  <span className={styles.move}>
                    {m.from_category_name} → <strong>{m.to_category_name}</strong>
                  </span>
                </li>
              ))}
            </ul>
          )}
          {preview.moves.length > 12 && (
            <p className={styles.muted}>and {preview.moves.length - 12} more…</p>
          )}
        </>
      )}

      {run.isError && <p className={styles.errorBanner}>Could not run the rules.</p>}

      <div className={styles.actions}>
        <button type="button" className={styles.cancelButton} onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.primaryButton}
          disabled={run.isPending || !preview || preview.candidate_count === 0}
          onClick={apply}
          data-testid="confirm-recategorize-all"
        >
          {run.isPending ? 'Working…' : 'Apply'}
        </button>
      </div>
    </Modal>
  )
}
