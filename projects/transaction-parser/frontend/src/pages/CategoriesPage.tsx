import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { useBuckets } from '../api/hooks/useBuckets'
import { useCategories } from '../api/hooks/useCategories'
import {
  useAddKeyword,
  useCreateCategory,
  useDeleteCategory,
  useDeleteKeyword,
  usePatchCategory,
} from '../api/hooks/useCategoryMutations'
import type { Category } from '../api/types'
import { ImpactPreviewDialog } from '../components/ImpactPreviewDialog/ImpactPreviewDialog'
import { Modal } from '../components/Modal/Modal'
import { PlusIcon } from '../components/icons'
import { Tabs } from '../components/Tabs/Tabs'
import { BucketsPanel } from './CategoriesPage/BucketsPanel'
import styles from './CategoriesPage.module.css'

interface PendingAddKeyword {
  categoryId: number
  categoryName: string
  keyword: string
}

interface PendingRemoveKeyword {
  categoryId: number
  categoryName: string
  keywordId: number
  keyword: string
}

interface PendingDelete {
  category: Category
}

function CategoryRow({
  category,
  onToast,
}: {
  category: Category
  onToast: (message: string) => void
}) {
  const [nameDraft, setNameDraft] = useState(category.name)
  const [keywordDraft, setKeywordDraft] = useState('')
  const [pendingAdd, setPendingAdd] = useState<PendingAddKeyword | null>(null)
  const [pendingRemove, setPendingRemove] = useState<PendingRemoveKeyword | null>(null)
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null)

  const patchCategory = usePatchCategory()
  const deleteCategory = useDeleteCategory()
  const addKeyword = useAddKeyword()
  const deleteKeyword = useDeleteKeyword()
  const { data: buckets } = useBuckets()

  useEffect(() => setNameDraft(category.name), [category.name])

  const commitRename = () => {
    const trimmed = nameDraft.trim()
    if (!trimmed || trimmed === category.name) {
      setNameDraft(category.name)
      return
    }
    patchCategory.mutate(
      { id: category.id, patch: { name: trimmed } },
      {
        onSuccess: (res) => {
          onToast(
            `Renamed to "${res.category.name}" — ${res.affected_transaction_count} transaction${
              res.affected_transaction_count === 1 ? '' : 's'
            } affected.`,
          )
        },
        onError: (err) => {
          setNameDraft(category.name)
          onToast(err instanceof ApiError ? err.message : 'Rename failed.')
        },
      },
    )
  }

  const submitAddKeyword = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = keywordDraft.trim()
    if (!trimmed) return
    setPendingAdd({ categoryId: category.id, categoryName: category.name, keyword: trimmed })
  }

  return (
    <div className={styles.row} data-testid="category-row" data-category-name={category.name}>
      <div className={styles.nameCol}>
        <div className={styles.nameRow}>
          <input
            className={styles.nameInput}
            value={nameDraft}
            disabled={category.is_system}
            onChange={(e) => setNameDraft(e.target.value)}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitRename()
              if (e.key === 'Escape') setNameDraft(category.name)
            }}
            aria-label={`Rename ${category.name}`}
            data-testid="category-name-input"
          />
          {category.is_system && <span className={styles.badge}>System</span>}
          {category.excluded_from_analytics && (
            <span className={`${styles.badge} ${styles.badgeExcluded}`}>Excluded</span>
          )}
        </div>
        <span className={styles.meta}>
          {category.transaction_count} transaction{category.transaction_count === 1 ? '' : 's'} ·{' '}
          {category.keywords.length} keyword{category.keywords.length === 1 ? '' : 's'} · priority{' '}
          {category.priority}
        </span>
        <select
          className={styles.groupSelect}
          value={category.bucket_id}
          onChange={(e) =>
            patchCategory.mutate({ id: category.id, patch: { bucket_id: Number(e.target.value) } })
          }
          aria-label={`Bucket for ${category.name}`}
          data-testid="category-group-select"
        >
          {(buckets ?? []).map((bucket) => (
            <option key={bucket.id} value={bucket.id}>
              {bucket.name}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.keywordCol}>
        {category.keywords.map((kw) => (
          <span className={styles.keywordChip} key={kw.id}>
            {kw.keyword}
            <button
              type="button"
              className={styles.keywordRemove}
              aria-label={`Remove keyword ${kw.keyword}`}
              onClick={() =>
                setPendingRemove({
                  categoryId: category.id,
                  categoryName: category.name,
                  keywordId: kw.id,
                  keyword: kw.keyword,
                })
              }
            >
              &times;
            </button>
          </span>
        ))}
        <form className={styles.addKeywordForm} onSubmit={submitAddKeyword}>
          <input
            className={styles.addKeywordInput}
            placeholder="Add keyword…"
            value={keywordDraft}
            onChange={(e) => setKeywordDraft(e.target.value)}
            aria-label={`Add keyword to ${category.name}`}
            data-testid="add-keyword-input"
          />
          <button type="submit" className={styles.addKeywordButton} data-testid="add-keyword-submit">
            <PlusIcon size={11} /> Add
          </button>
        </form>
      </div>

      <div className={styles.actionsCol}>
        {!category.is_system && (
          <button
            type="button"
            className={styles.deleteButton}
            onClick={() => setPendingDelete({ category })}
            data-testid="category-delete-button"
          >
            Delete
          </button>
        )}
      </div>

      {pendingAdd && (
        <ImpactPreviewDialog
          action="add_keyword"
          categoryId={pendingAdd.categoryId}
          categoryName={pendingAdd.categoryName}
          keyword={pendingAdd.keyword}
          isCommitting={addKeyword.isPending}
          commitError={
            addKeyword.isError
              ? addKeyword.error instanceof ApiError
                ? addKeyword.error.message
                : 'Could not add keyword.'
              : null
          }
          onCancel={() => {
            setPendingAdd(null)
            addKeyword.reset()
          }}
          onConfirm={(applyToExisting) => {
            addKeyword.mutate(
              {
                categoryId: pendingAdd.categoryId,
                body: { keyword: pendingAdd.keyword, apply_to_existing: applyToExisting },
              },
              {
                onSuccess: (res) => {
                  setKeywordDraft('')
                  setPendingAdd(null)
                  addKeyword.reset()
                  onToast(
                    `Added "${res.keyword.keyword}"${
                      res.applied_count > 0 ? ` — ${res.applied_count} transaction${res.applied_count === 1 ? '' : 's'} moved.` : '.'
                    }`,
                  )
                },
              },
            )
          }}
        />
      )}

      {pendingRemove && (
        <ImpactPreviewDialog
          action="remove_keyword"
          categoryId={pendingRemove.categoryId}
          categoryName={pendingRemove.categoryName}
          keyword={pendingRemove.keyword}
          isCommitting={deleteKeyword.isPending}
          commitError={
            deleteKeyword.isError
              ? deleteKeyword.error instanceof ApiError
                ? deleteKeyword.error.message
                : 'Could not remove keyword.'
              : null
          }
          onCancel={() => {
            setPendingRemove(null)
            deleteKeyword.reset()
          }}
          onConfirm={(reapply) => {
            deleteKeyword.mutate(
              { categoryId: pendingRemove.categoryId, keywordId: pendingRemove.keywordId, reapply },
              {
                onSuccess: (res) => {
                  setPendingRemove(null)
                  deleteKeyword.reset()
                  onToast(
                    `Removed "${pendingRemove.keyword}"${
                      res.reapplied_count > 0
                        ? ` — ${res.reapplied_count} transaction${res.reapplied_count === 1 ? '' : 's'} re-categorized.`
                        : '.'
                    }`,
                  )
                },
              },
            )
          }}
        />
      )}

      {pendingDelete && (
        <Modal title="Delete category?" onClose={() => setPendingDelete(null)} ariaLabel="Confirm delete category">
          <p className={styles.confirmBody}>
            Deleting <strong>{pendingDelete.category.name}</strong> will reassign its{' '}
            {pendingDelete.category.transaction_count} transaction
            {pendingDelete.category.transaction_count === 1 ? '' : 's'} to Uncategorized and remove
            its {pendingDelete.category.keywords.length} keyword
            {pendingDelete.category.keywords.length === 1 ? '' : 's'}. This cannot be undone.
          </p>
          {deleteCategory.isError && (
            <p className={styles.errorBanner}>
              {deleteCategory.error instanceof ApiError
                ? deleteCategory.error.message
                : 'Could not delete category.'}
            </p>
          )}
          <div className={styles.confirmActions}>
            <button type="button" className={styles.cancelButton} onClick={() => setPendingDelete(null)}>
              Cancel
            </button>
            <button
              type="button"
              className={styles.dangerButton}
              disabled={deleteCategory.isPending}
              data-testid="confirm-delete-category"
              onClick={() =>
                deleteCategory.mutate(pendingDelete.category.id, {
                  onSuccess: (res) => {
                    setPendingDelete(null)
                    onToast(
                      `Deleted "${pendingDelete.category.name}" — ${res.reassigned_transaction_count} transaction${
                        res.reassigned_transaction_count === 1 ? '' : 's'
                      } moved to Uncategorized.`,
                    )
                  },
                })
              }
            >
              {deleteCategory.isPending ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function AddCategoryDialog({ onClose, onToast }: { onClose: () => void; onToast: (m: string) => void }) {
  const [name, setName] = useState('')
  const [excluded, setExcluded] = useState(false)
  const [bucketId, setBucketId] = useState<number | null>(null)
  const createCategory = useCreateCategory()
  const { data: buckets } = useBuckets()

  useEffect(() => {
    if (bucketId == null && buckets && buckets.length > 0) {
      const other = buckets.find((b) => b.name === 'OTHER')
      setBucketId(other?.id ?? buckets[0]!.id)
    }
  }, [buckets, bucketId])

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createCategory.mutate(
      { name: trimmed, excluded_from_analytics: excluded, bucket_id: bucketId ?? undefined },
      {
        onSuccess: (category) => {
          onToast(`Created "${category.name}".`)
          onClose()
        },
      },
    )
  }

  return (
    <Modal title="New category" onClose={onClose} ariaLabel="Add category">
      <form onSubmit={submit}>
        <div className={styles.formField}>
          <label className={styles.formLabel} htmlFor="new-category-name">
            Name
          </label>
          <input
            id="new-category-name"
            className={styles.formInput}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            placeholder="e.g. Subscriptions"
            data-testid="new-category-name-input"
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel} htmlFor="new-category-bucket">
            Bucket
          </label>
          <select
            id="new-category-bucket"
            className={styles.groupSelect}
            value={bucketId ?? ''}
            onChange={(e) => setBucketId(Number(e.target.value))}
            data-testid="new-category-bucket-select"
          >
            {(buckets ?? []).map((bucket) => (
              <option key={bucket.id} value={bucket.id}>
                {bucket.name}
              </option>
            ))}
          </select>
        </div>
        <label className={styles.formCheckboxRow}>
          <input type="checkbox" checked={excluded} onChange={(e) => setExcluded(e.target.checked)} />
          <span>Exclude from analytics (like Transfers &amp; Income)</span>
        </label>
        {createCategory.isError && (
          <p className={styles.errorBanner}>
            {createCategory.error instanceof ApiError ? createCategory.error.message : 'Could not create category.'}
          </p>
        )}
        <div className={styles.confirmActions} style={{ marginTop: 'var(--sp-5)' }}>
          <button type="button" className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={styles.addButton}
            disabled={!name.trim() || createCategory.isPending}
            data-testid="submit-create-category"
          >
            {createCategory.isPending ? 'Creating…' : 'Create category'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

type SortMode = 'name' | 'group' | 'keywords-desc' | 'keywords-asc' | 'transactions-desc' | 'transactions-asc'

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'name', label: 'Name (A–Z)' },
  { value: 'group', label: 'Bucket' },
  { value: 'keywords-desc', label: 'Keyword count (most first)' },
  { value: 'keywords-asc', label: 'Keyword count (fewest first)' },
  { value: 'transactions-desc', label: 'Transaction count (most first)' },
  { value: 'transactions-asc', label: 'Transaction count (fewest first)' },
]

function sortCategories(categories: Category[], mode: SortMode): Category[] {
  const sorted = [...categories]
  if (mode === 'group') {
    sorted.sort((a, b) => (a.group ?? 'OTHER').localeCompare(b.group ?? 'OTHER') || a.name.localeCompare(b.name))
  } else if (mode === 'keywords-desc') {
    sorted.sort((a, b) => b.keywords.length - a.keywords.length || a.name.localeCompare(b.name))
  } else if (mode === 'keywords-asc') {
    sorted.sort((a, b) => a.keywords.length - b.keywords.length || a.name.localeCompare(b.name))
  } else if (mode === 'transactions-desc') {
    sorted.sort((a, b) => b.transaction_count - a.transaction_count || a.name.localeCompare(b.name))
  } else if (mode === 'transactions-asc') {
    sorted.sort((a, b) => a.transaction_count - b.transaction_count || a.name.localeCompare(b.name))
  } else {
    sorted.sort((a, b) => a.name.localeCompare(b.name))
  }
  return sorted
}

const TAB_ITEMS = [
  { key: 'categories', label: 'Categories' },
  { key: 'buckets', label: 'Buckets' },
]

export function CategoriesPage() {
  const { data: categories, isLoading, isError, error } = useCategories()
  const [showAdd, setShowAdd] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const [sortMode, setSortMode] = useState<SortMode>('name')
  const [activeTab, setActiveTab] = useState<string>('categories')
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = (message: string) => {
    setToast(message)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 4000)
  }

  useEffect(() => () => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
  }, [])

  const sorted = sortCategories(categories ?? [], sortMode)

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Categories</h1>
      </header>

      <div className={styles.tabsLayout}>
        <Tabs
          items={TAB_ITEMS}
          activeKey={activeTab}
          onChange={setActiveTab}
          orientation="horizontal"
          variant="folder"
          ariaLabel="Categories sections"
        />

        <div className={styles.tabContent}>
          {activeTab === 'categories' ? (
            <div role="tabpanel" id="tabpanel-categories" aria-labelledby="tab-categories">
              <div className={styles.headerActions}>
                <div className={styles.sortField}>
                  <label className={styles.sortLabel} htmlFor="categories-sort">
                    Sort by
                  </label>
                  <select
                    id="categories-sort"
                    className={styles.sortSelect}
                    value={sortMode}
                    onChange={(e) => setSortMode(e.target.value as SortMode)}
                    data-testid="categories-sort-select"
                  >
                    {SORT_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="button"
                  className={styles.addButton}
                  onClick={() => setShowAdd(true)}
                  data-testid="open-add-category"
                >
                  <PlusIcon /> Add category
                </button>
              </div>

              {isError && (
                <p className={styles.errorBanner}>
                  {error instanceof ApiError ? error.message : 'Could not load categories.'}
                </p>
              )}

              {isLoading ? (
                <p className={styles.meta}>Loading…</p>
              ) : (
                <div className={styles.list}>
                  {sorted.map((category) => (
                    <CategoryRow key={category.id} category={category} onToast={showToast} />
                  ))}
                </div>
              )}

              {showAdd && <AddCategoryDialog onClose={() => setShowAdd(false)} onToast={showToast} />}
            </div>
          ) : (
            <div role="tabpanel" id="tabpanel-buckets" aria-labelledby="tab-buckets">
              <BucketsPanel />
            </div>
          )}
        </div>
      </div>

      {toast && (
        <div className={styles.toast} data-testid="categories-toast">
          {toast}
        </div>
      )}
    </div>
  )
}
