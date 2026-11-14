import { useMemo } from 'react'
import type { Category } from '../../api/types'
import styles from './FilterBar.module.css'

const GROUP_ORDER = ['Essentials', 'Lifestyle', 'Income', 'Savings', 'Transfers', 'Other']

interface GroupedCategoryFilterProps {
  categories: Category[]
  selected: number[]
  onToggle: (categoryId: number) => void
}

/** The category filter as pills grouped under their category's `group`
 * label (Essentials/Lifestyle/Income/Savings/Transfers/Other), themed
 * through the same tokens as every other chip — grouping only changes
 * layout, not color. Categories with no group (user-created via the
 * quick-add flow) land in "Other". */
export function GroupedCategoryFilter({ categories, selected, onToggle }: GroupedCategoryFilterProps) {
  const grouped = useMemo(() => {
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
  }, [categories])

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
