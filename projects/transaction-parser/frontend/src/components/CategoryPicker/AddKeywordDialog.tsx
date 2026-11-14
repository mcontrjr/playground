import { useEffect, useState } from 'react'
import { useAddKeyword, useImpactPreview } from '../../api/hooks/useCategoryMutations'
import { Modal } from '../Modal/Modal'
import { cleanToken } from './cleanToken'
import styles from './CategoryPicker.module.css'

/** The "also add a keyword?" follow-up offered right after a manual
 * recategorization, prefilled with a cleaned token from the
 * description. Rendered as a page-level Modal (not inline in the
 * transaction's row) specifically so it survives the row it was
 * triggered from disappearing from the list — which happens whenever
 * the active filter excludes the transaction's NEW category (most
 * commonly: filtering Records by "Uncategorized" and then
 * recategorizing a row away from it). An inline/row-scoped version of
 * this prompt would unmount along with the row before the user ever
 * saw it. */
export function AddKeywordDialog({
  categoryId,
  categoryName,
  description,
  onDone,
}: {
  categoryId: number
  categoryName: string
  description: string
  onDone: () => void
}) {
  const [keyword, setKeyword] = useState(() => cleanToken(description))
  const [dirty, setDirty] = useState(false)
  const preview = useImpactPreview()
  const addKeyword = useAddKeyword()

  const runPreview = (value: string) => {
    if (!value.trim()) return
    preview.mutate({ action: 'add_keyword', category_id: categoryId, keyword: value.trim() })
  }

  useEffect(() => {
    runPreview(keyword)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleKeywordChange = (value: string) => {
    setKeyword(value)
    setDirty(true)
  }

  const commit = () => {
    const trimmed = keyword.trim()
    if (!trimmed) return
    addKeyword.mutate(
      { categoryId, body: { keyword: trimmed, apply_to_existing: true } },
      { onSuccess: onDone },
    )
  }

  return (
    <Modal title="Add a keyword?" onClose={onDone} ariaLabel="Add a keyword for this category">
      <p className={styles.followUpDescription}>{description}</p>
      <p className={styles.followUpText}>
        Also add <strong>"{keyword || '…'}"</strong> as a keyword for {categoryName}, so future
        imports match automatically?
      </p>
      <div className={styles.followUpRow}>
        <input
          className={styles.followUpInput}
          value={keyword}
          autoFocus
          onChange={(e) => handleKeywordChange(e.target.value)}
          onBlur={() => dirty && runPreview(keyword)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              runPreview(keyword)
              setDirty(false)
            }
          }}
          aria-label="Keyword"
        />
        <span className={styles.followUpCount}>
          {preview.isPending
            ? '…'
            : preview.data
              ? `${preview.data.affected_count} match${preview.data.affected_count === 1 ? '' : 'es'}`
              : ''}
        </span>
      </div>
      {addKeyword.isError && <p className={styles.followUpError}>Couldn't add — keyword may be taken.</p>}
      <div className={styles.followUpActions}>
        <button
          type="button"
          className={styles.followUpDismiss}
          onClick={onDone}
          data-testid="followup-dismiss"
        >
          Not now
        </button>
        <button
          type="button"
          className={styles.followUpConfirm}
          disabled={!keyword.trim() || addKeyword.isPending || preview.isPending}
          onClick={commit}
        >
          {addKeyword.isPending ? 'Adding…' : 'Add keyword'}
        </button>
      </div>
    </Modal>
  )
}
