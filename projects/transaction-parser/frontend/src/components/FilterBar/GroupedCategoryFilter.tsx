import { useMemo } from 'react'
import { useBuckets } from '../../api/hooks/useBuckets'
import type { Category } from '../../api/types'
import styles from './FilterBar.module.css'

interface GroupedCategoryFilterProps {
  categories: Category[]
  selected: number[]
  onToggle: (categoryId: number) => void
}

/** The category filter as pills grouped under their category's bucket
 * (`group`, the uppercase bucket name), themed through the same
 * tokens as every other chip — grouping only changes layout, not
 * color. Ordering comes from `useBuckets()` (name-sorted, OTHER
 * always exists as the fallback bucket) instead of a hardcoded list,
 * since buckets are now user-managed. */
export function GroupedCategoryFilter({ categories, selected, onToggle }: GroupedCategoryFilterProps) {
  const { data: buckets } = useBuckets()

  const grouped = useMemo(() => {
    const byGroup = new Map<string, Category[]>()
    for (const category of categories) {
      const group = category.group ?? 'OTHER'
      const list = byGroup.get(group) ?? []
      list.push(category)
      byGroup.set(group, list)
    }
    const bucketOrder = (buckets ?? []).map((b) => b.name)
    const known = bucketOrder.filter((g) => byGroup.has(g))
    const unknown = [...byGroup.keys()].filter((g) => !bucketOrder.includes(g)).sort()
    return [...known, ...unknown].map((group) => ({ group, items: byGroup.get(group)! }))
  }, [categories, buckets])

  if (categories.length === 0) {
    return (
      <div className={styles.field}>
        <span className={styles.fieldLabel}>Category</span>
        <span className={styles.emptyHint}>None yet</span>
      </div>
    )
  }

  return (
    <div className={styles.field}>
      <span className={styles.fieldLabel}>Category</span>
      <div className={styles.categoryGroups} role="group" aria-label="Filter by category">
        {grouped.map(({ group, items }) => (
          <div key={group} className={styles.categoryGroup}>
            <span className={styles.categoryGroupLabel}>{group}</span>
            <div className={styles.multiSelect}>
              {items.map((category) => {
                const isActive = selected.includes(category.id)
                return (
                  <button
                    key={category.id}
                    type="button"
                    className={isActive ? `${styles.chip} ${styles.chipActive}` : styles.chip}
                    onClick={() => onToggle(category.id)}
                    aria-pressed={isActive}
                  >
                    {category.name}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
