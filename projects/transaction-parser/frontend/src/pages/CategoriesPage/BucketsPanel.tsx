import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../../api/client'
import { useBuckets } from '../../api/hooks/useBuckets'
import { useCreateBucket, useDeleteBucket, usePatchBucket } from '../../api/hooks/useBucketMutations'
import { useCategories } from '../../api/hooks/useCategories'
import { usePatchCategory } from '../../api/hooks/useCategoryMutations'
import type { Bucket, Category } from '../../api/types'
import { Modal } from '../../components/Modal/Modal'
import { PlusIcon } from '../../components/icons'
import styles from './BucketsPanel.module.css'

const OTHER_BUCKET_NAME = 'OTHER'
const DRAG_CATEGORY_MIME = 'application/x-category-id'

interface PendingDelete {
  bucket: Bucket
}

function CategoryChip({ category }: { category: Category }) {
  const [isDragging, setIsDragging] = useState(false)

  return (
    <span
      className={isDragging ? `${styles.categoryChip} ${styles.categoryChipDragging}` : styles.categoryChip}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData(DRAG_CATEGORY_MIME, String(category.id))
        e.dataTransfer.effectAllowed = 'move'
        setIsDragging(true)
      }}
      onDragEnd={() => setIsDragging(false)}
      data-testid="bucket-category-chip"
      data-category-id={category.id}
    >
      {category.name}
    </span>
  )
}

function BucketRow({
  bucket,
  categories,
  onToast,
  onRequestDelete,
  onDropCategory,
}: {
  bucket: Bucket
  categories: Category[]
  onToast: (message: string) => void
  onRequestDelete: (bucket: Bucket) => void
  onDropCategory: (categoryId: number, bucket: Bucket) => void
}) {
  const [nameDraft, setNameDraft] = useState(bucket.name)
  const [isDropTarget, setIsDropTarget] = useState(false)
  const patchBucket = usePatchBucket()
  const isOther = bucket.name === OTHER_BUCKET_NAME

  useEffect(() => setNameDraft(bucket.name), [bucket.name])

  const commitRename = () => {
    const trimmed = nameDraft.trim().toUpperCase()
    if (!trimmed || trimmed === bucket.name) {
      setNameDraft(bucket.name)
      return
    }
    patchBucket.mutate(
      { id: bucket.id, patch: { name: trimmed } },
      {
        onSuccess: (updated) => onToast(`Renamed to "${updated.name}".`),
        onError: (err) => {
          setNameDraft(bucket.name)
          onToast(err instanceof ApiError ? err.message : 'Rename failed.')
        },
      },
    )
  }

  return (
    <div
      className={isDropTarget ? `${styles.rowGroup} ${styles.rowGroupDropTarget}` : styles.rowGroup}
      data-testid="bucket-row"
      data-bucket-name={bucket.name}
      onDragOver={(e) => {
        if (!e.dataTransfer.types.includes(DRAG_CATEGORY_MIME)) return
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
        setIsDropTarget(true)
      }}
      onDragLeave={() => setIsDropTarget(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDropTarget(false)
        const categoryId = Number(e.dataTransfer.getData(DRAG_CATEGORY_MIME))
        if (categoryId) onDropCategory(categoryId, bucket)
      }}
    >
      <div className={styles.row}>
        <div className={styles.nameCol}>
          <input
            className={styles.nameInput}
            value={nameDraft}
            disabled={isOther}
            onChange={(e) => setNameDraft(e.target.value.toUpperCase())}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitRename()
              if (e.key === 'Escape') setNameDraft(bucket.name)
            }}
            aria-label={`Rename ${bucket.name}`}
            data-testid="bucket-name-input"
          />
          <span className={styles.meta}>
            {bucket.category_count} categor{bucket.category_count === 1 ? 'y' : 'ies'}
          </span>
        </div>

        {!isOther && (
          <div className={styles.actions}>
            <button
              type="button"
              className={styles.deleteButton}
              onClick={() => onRequestDelete(bucket)}
              data-testid="bucket-delete-button"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      <div className={styles.categoryDropZone}>
        {categories.length > 0 ? (
          categories.map((category) => <CategoryChip key={category.id} category={category} />)
        ) : (
          <span className={styles.categoryDropHint}>Drag categories here</span>
        )}
      </div>
    </div>
  )
}

function AddBucketDialog({ onClose, onToast }: { onClose: () => void; onToast: (m: string) => void }) {
  const [name, setName] = useState('')
  const createBucket = useCreateBucket()

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createBucket.mutate(
      { name: trimmed },
      {
        onSuccess: (bucket) => {
          onToast(`Created "${bucket.name}".`)
          onClose()
        },
      },
    )
  }

  return (
    <Modal title="New bucket" onClose={onClose} ariaLabel="Add bucket">
      <form onSubmit={submit}>
        <div className={styles.formField}>
          <label className={styles.formLabel} htmlFor="new-bucket-name">
            Name
          </label>
          <input
            id="new-bucket-name"
            className={styles.formInput}
            value={name}
            onChange={(e) => setName(e.target.value.toUpperCase())}
            autoFocus
            placeholder="e.g. SUBSCRIPTIONS"
            data-testid="new-bucket-name-input"
          />
        </div>
        {createBucket.isError && (
          <p className={styles.errorBanner}>
            {createBucket.error instanceof ApiError ? createBucket.error.message : 'Could not create bucket.'}
          </p>
        )}
        <div className={styles.confirmActions}>
          <button type="button" className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={styles.addButton}
            disabled={!name.trim() || createBucket.isPending}
            data-testid="submit-create-bucket"
          >
            {createBucket.isPending ? 'Creating…' : 'Create bucket'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function DeleteBucketDialog({
  bucket,
  buckets,
  onClose,
  onToast,
}: {
  bucket: Bucket
  buckets: Bucket[]
  onClose: () => void
  onToast: (m: string) => void
}) {
  const otherBucket = buckets.find((b) => b.name === OTHER_BUCKET_NAME)
  const [reassignTo, setReassignTo] = useState<number>(otherBucket?.id ?? buckets[0]?.id ?? bucket.id)
  const deleteBucket = useDeleteBucket()

  const candidates = buckets.filter((b) => b.id !== bucket.id)

  return (
    <Modal title="Delete bucket?" onClose={onClose} ariaLabel="Confirm delete bucket">
      <p className={styles.confirmBody}>
        Deleting <strong>{bucket.name}</strong> will move its {bucket.category_count} categor
        {bucket.category_count === 1 ? 'y' : 'ies'} to another bucket. This cannot be undone.
      </p>
      <div className={styles.formField}>
        <label className={styles.formLabel} htmlFor="reassign-bucket-select">
          Move its categories to
        </label>
        <select
          id="reassign-bucket-select"
          className={styles.formSelect}
          value={reassignTo}
          onChange={(e) => setReassignTo(Number(e.target.value))}
          data-testid="reassign-bucket-select"
        >
          {candidates.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>
      {deleteBucket.isError && (
        <p className={styles.errorBanner}>
          {deleteBucket.error instanceof ApiError ? deleteBucket.error.message : 'Could not delete bucket.'}
        </p>
      )}
      <div className={styles.confirmActions}>
        <button type="button" className={styles.cancelButton} onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className={styles.dangerButton}
          disabled={deleteBucket.isPending}
          data-testid="confirm-delete-bucket"
          onClick={() =>
            deleteBucket.mutate(
              { id: bucket.id, reassignToBucketId: reassignTo },
              {
                onSuccess: (res) => {
                  onClose()
                  onToast(
                    `Deleted "${bucket.name}" — ${res.moved_category_count} categor${
                      res.moved_category_count === 1 ? 'y' : 'ies'
                    } moved.`,
                  )
                },
              },
            )
          }
        >
          {deleteBucket.isPending ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </Modal>
  )
}

export function BucketsPanel() {
  const { data: buckets, isLoading, isError, error } = useBuckets()
  const { data: categories } = useCategories()
  const [showAdd, setShowAdd] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const patchCategory = usePatchCategory()

  const showToast = (message: string) => {
    setToast(message)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 4000)
  }

  useEffect(() => () => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
  }, [])

  const sorted = [...(buckets ?? [])].sort((a, b) => a.name.localeCompare(b.name))

  const categoriesByBucket = new Map<number, Category[]>()
  for (const category of categories ?? []) {
    const list = categoriesByBucket.get(category.bucket_id)
    if (list) list.push(category)
    else categoriesByBucket.set(category.bucket_id, [category])
  }
  for (const list of categoriesByBucket.values()) {
    list.sort((a, b) => a.name.localeCompare(b.name))
  }

  const handleDropCategory = (categoryId: number, bucket: Bucket) => {
    const category = (categories ?? []).find((c) => c.id === categoryId)
    if (!category || category.bucket_id === bucket.id) return
    patchCategory.mutate(
      { id: categoryId, patch: { bucket_id: bucket.id } },
      {
        onSuccess: () => showToast(`Moved "${category.name}" to ${bucket.name}.`),
        onError: (err) => showToast(err instanceof ApiError ? err.message : 'Could not move category.'),
      },
    )
  }

  return (
    <div>
      <div className={styles.header}>
        <h2 className={styles.heading}>Buckets</h2>
        <button
          type="button"
          className={styles.addButton}
          onClick={() => setShowAdd(true)}
          data-testid="open-add-bucket"
        >
          <PlusIcon /> Add bucket
        </button>
      </div>

      {isError && (
        <p className={styles.errorBanner}>
          {error instanceof ApiError ? error.message : 'Could not load buckets.'}
        </p>
      )}

      {isLoading ? (
        <p className={styles.meta}>Loading…</p>
      ) : (
        <div className={styles.list}>
          {sorted.map((bucket) => (
            <BucketRow
              key={bucket.id}
              bucket={bucket}
              categories={categoriesByBucket.get(bucket.id) ?? []}
              onToast={showToast}
              onRequestDelete={(b) => setPendingDelete({ bucket: b })}
              onDropCategory={handleDropCategory}
            />
          ))}
        </div>
      )}

      {showAdd && <AddBucketDialog onClose={() => setShowAdd(false)} onToast={showToast} />}

      {pendingDelete && (
        <DeleteBucketDialog
          bucket={pendingDelete.bucket}
          buckets={buckets ?? []}
          onClose={() => setPendingDelete(null)}
          onToast={showToast}
        />
      )}

      {toast && (
        <div className={styles.toast} data-testid="buckets-toast">
          {toast}
        </div>
      )}
    </div>
  )
}
