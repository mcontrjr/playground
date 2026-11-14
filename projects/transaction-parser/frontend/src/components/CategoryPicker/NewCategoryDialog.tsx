import { useState } from 'react'
import { useCreateCategory } from '../../api/hooks/useCategoryMutations'
import type { Category } from '../../api/types'
import { Modal } from '../Modal/Modal'
import { cleanToken } from './cleanToken'
import styles from './CategoryPicker.module.css'

/** Inline "create a category right from this transaction" dialog — the
 * quick path Records wants, instead of sending the user to the
 * Categories page and back. Rendered as a page-level Modal for the
 * same reason as AddKeywordDialog: it must not live inside the
 * transaction's table row, which can disappear out from under it. */
export function NewCategoryDialog({
  description,
  onCreated,
  onCancel,
}: {
  description: string
  onCreated: (category: Category) => void
  onCancel: () => void
}) {
  const [name, setName] = useState('')
  const createCategory = useCreateCategory()

  const commit = () => {
    const trimmed = name.trim()
    if (!trimmed) return
    createCategory.mutate({ name: trimmed }, { onSuccess: onCreated })
  }

  return (
    <Modal title="New category" onClose={onCancel} ariaLabel="Create a new category">
      <p className={styles.followUpDescription}>{description}</p>
      <p className={styles.followUpText}>
        New category for <strong>"{cleanToken(description)}"</strong>
      </p>
      <div className={styles.followUpRow}>
        <input
          className={styles.followUpInput}
          value={name}
          autoFocus
          placeholder="Category name…"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              commit()
            }
            if (e.key === 'Escape') onCancel()
          }}
          aria-label="New category name"
        />
      </div>
      {createCategory.isError && (
        <p className={styles.followUpError}>Couldn't create — that name may be taken.</p>
      )}
      <div className={styles.followUpActions}>
        <button type="button" className={styles.followUpDismiss} onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.followUpConfirm}
          disabled={!name.trim() || createCategory.isPending}
          onClick={commit}
        >
          {createCategory.isPending ? 'Creating…' : 'Create & apply'}
        </button>
      </div>
    </Modal>
  )
}
