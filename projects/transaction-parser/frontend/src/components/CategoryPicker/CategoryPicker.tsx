import { useEffect, useMemo, useState } from 'react'
import { useCategories } from '../../api/hooks/useCategories'
import { usePatchTransaction } from '../../api/hooks/usePatchTransaction'
import type { Category } from '../../api/types'
import styles from './CategoryPicker.module.css'

const NEW_CATEGORY_VALUE = '__new__'
const GROUP_ORDER = ['Essentials', 'Lifestyle', 'Income', 'Savings', 'Transfers', 'Other']

export interface RecategorizedInfo {
  categoryId: number
  categoryName: string
  isSystem: boolean
}

interface CategoryPickerProps {
  transactionId: number
  categoryId: number | null
  /** Fired after a successful recategorization. Owned by the page, not
   * this component — this row (and this CategoryPicker instance) can
   * be unmounted a moment later if the active filter now excludes the
   * transaction's new category (e.g. filtering by "Uncategorized" and
   * then picking a real category), so any "add a keyword?" follow-up
   * must live in state that outlives the row, not state local to it. */
  onRecategorized: (info: RecategorizedInfo) => void
  /** Fired when the user picks "+ New category…" — the create dialog
   * is rendered by the page for the same row-survival reason. */
  onRequestNewCategory: () => void
}

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

export function CategoryPicker({
  transactionId,
  categoryId,
  onRecategorized,
  onRequestNewCategory,
}: CategoryPickerProps) {
  const { data: categories } = useCategories()
  const patchTransaction = usePatchTransaction()
  const [flash, setFlash] = useState(false)

  const grouped = useMemo(() => groupCategories(categories ?? []), [categories])

  useEffect(() => {
    if (!flash) return
    const timeout = setTimeout(() => setFlash(false), 900)
    return () => clearTimeout(timeout)
  }, [flash])

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    if (event.target.value === NEW_CATEGORY_VALUE) {
      onRequestNewCategory()
      return
    }
    const nextCategoryId = Number(event.target.value)
    const category = categories?.find((c) => c.id === nextCategoryId)
    if (!category) return
    patchTransaction.mutate(
      { id: transactionId, patch: { category_id: category.id } },
      {
        onSuccess: () => {
          setFlash(true)
          onRecategorized({
            categoryId: category.id,
            categoryName: category.name,
            isSystem: category.is_system,
          })
        },
      },
    )
  }

  return (
    <span className={styles.wrap}>
      <select
        className={`${styles.select} ${flash ? styles.flashSuccess : ''} ${
          categoryId === null ? styles.uncategorized : ''
        }`}
        value={categoryId ?? ''}
        onChange={handleChange}
        disabled={patchTransaction.isPending}
        aria-label="Category"
        data-testid="category-picker-select"
      >
        {categoryId === null && <option value="">Uncategorized</option>}
        {grouped.map(({ group, items }) => (
          <optgroup key={group} label={group}>
            {items.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </optgroup>
        ))}
        <option value={NEW_CATEGORY_VALUE}>+ New category…</option>
      </select>
    </span>
  )
}
