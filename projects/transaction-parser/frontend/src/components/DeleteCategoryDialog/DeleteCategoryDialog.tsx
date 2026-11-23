import { useState } from 'react'
import { ApiError } from '../../api/client'
import { useDeleteCategory } from '../../api/hooks/useCategoryMutations'
import { useDeleteCategoryPreview } from '../../api/hooks/useClashes'
import type { Category } from '../../api/types'
import { Modal } from '../Modal/Modal'
import styles from './DeleteCategoryDialog.module.css'

interface DeleteCategoryDialogProps {
  category: Category
  onCancel: () => void
  onDone: (message: string) => void
}

/** Delete confirm with an impact preview.
 *
 * Deleting a category takes its keywords with it, so its transactions
 * have to go somewhere. Two outcomes are possible and the user picks:
 *
 * - **Re-match** (default): re-run the remaining rules, so a row whose
 *   text another category already claims lands there instead of in
 *   Uncategorized. Rows nothing matches still fall to Uncategorized.
 * - **Move all to Uncategorized**: the old behavior, kept because
 *   parking everything in one place is sometimes the point.
 *
 * Either way manual/bulk rows are never re-matched — they come off the
 * deleted category (the row can't keep pointing at it) but the rules
 * don't get to re-decide a category a person chose. */
export function DeleteCategoryDialog({ category, onCancel, onDone }: DeleteCategoryDialogProps) {
  const [rematch, setRematch] = useState(true)
  const deleteCategory = useDeleteCategory()
  const preview = useDeleteCategoryPreview(category.id)

  const moves = preview.data
  // The preview only covers rule-eligible rows; the rest land in
  // Uncategorized regardless of the choice.
  const rematchable = (moves?.breakdown ?? []).filter(
    (entry) => entry.to_category !== 'Uncategorized',
  )
  const rematchableCount = rematchable.reduce((sum, entry) => sum + entry.count, 0)

  const confirm = () => {
    deleteCategory.mutate(
      { id: category.id, rematch },
      {
        onSuccess: (res) => {
          const moved = res.reassigned_transaction_count
          const rematched = res.rematched_transaction_count
          onDone(
            rematched > 0
              ? `Deleted "${category.name}" — ${rematched} of ${moved} record${moved === 1 ? '' : 's'} re-matched, the rest moved to Uncategorized.`
              : `Deleted "${category.name}" — ${moved} record${moved === 1 ? '' : 's'} moved to Uncategorized.`,
          )
        },
      },
    )
  }

  return (
    <Modal title="Delete category?" onClose={onCancel} ariaLabel="Confirm delete category" wide>
      <p className={styles.body}>
        Deleting <strong>{category.name}</strong> removes its{' '}
        {category.keywords.length} keyword{category.keywords.length === 1 ? '' : 's'} and
        reassigns its {category.transaction_count} transaction
        {category.transaction_count === 1 ? '' : 's'}. This cannot be undone.
      </p>

      {preview.isPending && <p className={styles.muted}>Checking where records would go…</p>}

      {moves && (
        <div className={styles.previewBox} data-testid="delete-preview">
          {rematchableCount > 0 ? (
            <>
              <p className={styles.previewTitle}>
                {rematchableCount} record{rematchableCount === 1 ? '' : 's'} match another
                category&apos;s keywords
              </p>
              <ul className={styles.breakdown}>
                {rematchable.map((entry) => (
                  <li key={`${entry.to_category_id}`} className={styles.breakdownRow}>
                    <span className={styles.count}>{entry.count}</span>
                    <span>→ {entry.to_category}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className={styles.previewTitle}>
              No remaining keywords claim these records — they will all go to Uncategorized.
            </p>
          )}
        </div>
      )}

      {rematchableCount > 0 && (
        <div className={styles.choice}>
          <label className={styles.choiceRow}>
            <input
              type="radio"
              name="delete-disposition"
              checked={rematch}
              onChange={() => setRematch(true)}
              data-testid="delete-rematch"
            />
            <span>
              Re-match to the categories above
              <span className={styles.hint}>Records nothing matches still go to Uncategorized.</span>
            </span>
          </label>
          <label className={styles.choiceRow}>
            <input
              type="radio"
              name="delete-disposition"
              checked={!rematch}
              onChange={() => setRematch(false)}
              data-testid="delete-no-rematch"
            />
            <span>
              Move everything to Uncategorized
              <span className={styles.hint}>Sort them out yourself later.</span>
            </span>
          </label>
        </div>
      )}

      {deleteCategory.isError && (
        <p className={styles.errorBanner}>
          {deleteCategory.error instanceof ApiError
            ? deleteCategory.error.message
            : 'Could not delete category.'}
        </p>
      )}

      <div className={styles.actions}>
        <button type="button" className={styles.cancelButton} onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.dangerButton}
          disabled={deleteCategory.isPending}
          data-testid="confirm-delete-category"
          onClick={confirm}
        >
          {deleteCategory.isPending ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </Modal>
  )
}
