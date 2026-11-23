import { useState } from 'react'
import { useReprioritize } from '../../api/hooks/useClashes'
import type { Category, ReprioritizeResponse } from '../../api/types'
import styles from './PriorityPanel.module.css'

interface PriorityPanelProps {
  categories: Category[]
  onToast: (message: string) => void
}

/** Reorder which category wins when two both match a description.
 *
 * Lower in this list = matched first. Two things make this more than a
 * sortable list, and both are called out in the UI:
 *
 * - Priority is *global*, so a reorder to fix one merchant can move
 *   unrelated rows sharing a keyword. Nothing is written until a dry-run
 *   preview has been shown and confirmed.
 * - Transfer keywords are matched before this ordering is consulted at
 *   all, so no position here can beat them.
 */
export function PriorityPanel({ categories, onToast }: PriorityPanelProps) {
  // Local working order, seeded from the server's priority ordering.
  const [order, setOrder] = useState<number[] | null>(null)
  const [dragId, setDragId] = useState<number | null>(null)
  const [preview, setPreview] = useState<ReprioritizeResponse | null>(null)
  const reprioritize = useReprioritize()

  const byId = new Map(categories.map((c) => [c.id, c]))
  const serverOrder = [...categories].sort((a, b) => a.priority - b.priority).map((c) => c.id)
  const working = order ?? serverOrder
  const isDirty = order !== null && order.join() !== serverOrder.join()

  const move = (fromId: number, toId: number) => {
    if (fromId === toId) return
    const next = [...working]
    const from = next.indexOf(fromId)
    const to = next.indexOf(toId)
    if (from === -1 || to === -1) return
    next.splice(to, 0, ...next.splice(from, 1))
    setOrder(next)
    setPreview(null)
  }

  /** Dense 0..n-1 priorities from the working order. Sent whole rather
   * than as a diff so the resulting order is exactly what's shown. */
  const priorityMap = (): Record<number, number> =>
    Object.fromEntries(working.map((id, index) => [id, index]))

  const runPreview = () => {
    reprioritize.mutate(
      { priorities: priorityMap(), dry_run: true },
      { onSuccess: setPreview },
    )
  }

  const apply = () => {
    reprioritize.mutate(
      { priorities: priorityMap(), dry_run: false },
      {
        onSuccess: (res) => {
          onToast(
            res.affected_count > 0
              ? `Match order saved — ${res.affected_count} record${res.affected_count === 1 ? '' : 's'} recategorized.`
              : 'Match order saved.',
          )
          setPreview(null)
          setOrder(null)
        },
      },
    )
  }

  const reset = () => {
    setOrder(null)
    setPreview(null)
    reprioritize.reset()
  }

  return (
    <section>
      <header className={styles.header}>
        <h3 className={styles.heading}>Match order</h3>
        <p className={styles.sub}>
          When a record matches more than one category, the one highest in
          this list wins. Drag to reorder, then preview before saving.
          Records you categorized by hand are never moved.
        </p>
        <p className={styles.note}>
          Payments &amp; Transfers keywords are matched before this order is
          consulted, so they win regardless of position here.
        </p>
      </header>

      <ol className={styles.list} data-testid="priority-list">
        {working.map((id, index) => {
          const category = byId.get(id)
          if (!category) return null
          return (
            <li
              key={id}
              className={dragId === id ? `${styles.item} ${styles.itemDragging}` : styles.item}
              draggable
              onDragStart={() => setDragId(id)}
              onDragEnd={() => setDragId(null)}
              onDragOver={(e) => {
                e.preventDefault()
                if (dragId !== null) move(dragId, id)
              }}
              data-testid="priority-item"
              data-category-name={category.name}
            >
              <span className={styles.rank}>{index + 1}</span>
              <span className={styles.name}>{category.name}</span>
              <span className={styles.count}>
                {category.keywords.length} keyword{category.keywords.length === 1 ? '' : 's'}
              </span>
              <span className={styles.grip} aria-hidden="true">
                ⋮⋮
              </span>
            </li>
          )
        })}
      </ol>

      {isDirty && (
        <div className={styles.bar} data-testid="priority-actions">
          {!preview ? (
            <>
              <span className={styles.barText}>Order changed.</span>
              <button
                type="button"
                className={styles.primary}
                onClick={runPreview}
                disabled={reprioritize.isPending}
                data-testid="priority-preview"
              >
                {reprioritize.isPending ? 'Checking…' : 'Preview impact'}
              </button>
              <button type="button" className={styles.secondary} onClick={reset}>
                Discard
              </button>
            </>
          ) : (
            <>
              <span className={styles.barText} data-testid="priority-preview-result">
                {preview.candidate_count === 0
                  ? 'No existing records would change.'
                  : `${preview.candidate_count} record${preview.candidate_count === 1 ? '' : 's'} would move.`}
              </span>
              <button
                type="button"
                className={styles.primary}
                onClick={apply}
                disabled={reprioritize.isPending}
                data-testid="priority-apply"
              >
                {reprioritize.isPending ? 'Saving…' : 'Save order'}
              </button>
              <button type="button" className={styles.secondary} onClick={reset}>
                Discard
              </button>
            </>
          )}
        </div>
      )}

      {preview && preview.moves.length > 0 && (
        <div className={styles.previewBox}>
          <p className={styles.previewTitle}>Records that would move</p>
          <ul className={styles.previewList}>
            {preview.moves.slice(0, 12).map((m) => (
              <li key={m.transaction_id} className={styles.previewRow}>
                <span className={styles.previewDesc} title={m.description}>
                  {m.description}
                </span>
                <span className={styles.previewMove}>
                  {m.from_category_name} → <strong>{m.to_category_name}</strong>
                </span>
              </li>
            ))}
          </ul>
          {preview.moves.length > 12 && (
            <p className={styles.previewMore}>
              and {preview.moves.length - 12} more…
            </p>
          )}
        </div>
      )}

      {reprioritize.isError && (
        <p className={styles.error}>Could not update match order.</p>
      )}
    </section>
  )
}
