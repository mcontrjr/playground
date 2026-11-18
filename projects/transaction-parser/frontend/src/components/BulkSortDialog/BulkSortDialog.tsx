import { useMemo, useState } from 'react'
import { useBulkRecategorize } from '../../api/hooks/useBulkRecategorize'
import { useCategories } from '../../api/hooks/useCategories'
import { ApiError } from '../../api/client'
import type { Category } from '../../api/types'
import { Modal } from '../Modal/Modal'
import styles from './BulkSortDialog.module.css'

const GROUP_ORDER = ['Essentials', 'Lifestyle', 'Income', 'Savings', 'Transfers', 'Other']

function groupCategories(categories: Category[]): { group: string; items: Category[] }[] {
  const byGroup = new Map<string, Category[]>()
  for (const category of categories) {
    const group = category.group ?? 'Other'
    const list = byGroup.get(group) ?? []
    list.push(category)
    byGroup.set(group, list)
  }
  const known = GROUP_ORDER.filter((g) => byGroup.has(g))
  const unknown = [...byGroup.keys()].filter((g) => !GROUP_ORDER.includes(g)).sort()
  return [...known, ...unknown].map((group) => ({ group, items: byGroup.get(group)! }))
}

interface BulkSortDialogProps {
  transactionIds: number[]
  onClose: () => void
  /** Fired after a successful bulk recategorize — distinct from
   * onClose so the caller can also clear its row-selection state,
   * mirroring AddKeywordDialog's onDone convention. */
  onDone: () => void
}

/** Bulk-sort confirmation modal: pick a target category, see the exact
 * count that will be affected, confirm once. Mirrors the
 * preview-then-confirm shape of ImpactPreviewDialog, but the "preview"
 * here is just the already-known selection count — no server round
 * trip needed before showing it, since the count is simply how many
 * rows the user checked. */
export function BulkSortDialog({ transactionIds, onClose, onDone }: BulkSortDialogProps) {
  const { data: categories } = useCategories()
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const bulkRecategorize = useBulkRecategorize()

  const grouped = useMemo(() => groupCategories(categories ?? []), [categories])
  const selectedCategory = categories?.find((c) => c.id === categoryId)
  const count = transactionIds.length

  const confirm = () => {
    if (categoryId === '') return
    bulkRecategorize.mutate(
      { transaction_ids: transactionIds, category_id: categoryId },
      { onSuccess: onDone },
    )
  }

  return (
    <Modal title="Bulk sort" onClose={onClose} ariaLabel="Bulk sort transactions">
      <div className={styles.formField}>
        <label className={styles.formLabel} htmlFor="bulk-sort-category">
          Move to category
        </label>
        <select
          id="bulk-sort-category"
          className={styles.select}
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : '')}
          autoFocus
          data-testid="bulk-sort-category-select"
        >
          <option value="" disabled>
            Choose a category…
          </option>
          {grouped.map(({ group, items }) => (
            <optgroup key={group} label={group}>
              {items.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      <p className={styles.previewText} data-testid="bulk-sort-preview">
        This will recategorize <strong>{count}</strong> transaction{count === 1 ? '' : 's'}
        {selectedCategory ? (
          <>
            {' '}
            to <strong>{selectedCategory.name}</strong>.
          </>
        ) : (
          '.'
        )}
      </p>

      {bulkRecategorize.isError && (
        <p className={styles.errorBanner}>
          {bulkRecategorize.error instanceof ApiError
            ? bulkRecategorize.error.message
            : 'Could not bulk sort these transactions.'}
        </p>
      )}

      <div className={styles.confirmActions}>
        <button type="button" className={styles.cancelButton} onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.confirmButton}
          disabled={categoryId === '' || bulkRecategorize.isPending}
          onClick={confirm}
          data-testid="confirm-bulk-sort"
        >
          {bulkRecategorize.isPending ? 'Sorting…' : `Sort ${count} transaction${count === 1 ? '' : 's'}`}
        </button>
      </div>
    </Modal>
  )
}
