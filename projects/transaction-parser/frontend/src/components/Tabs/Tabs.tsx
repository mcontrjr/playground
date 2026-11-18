import { useRef } from 'react'
import styles from './Tabs.module.css'

export interface TabItem {
  key: string
  label: string
}

interface TabsProps {
  items: TabItem[]
  activeKey: string
  onChange: (key: string) => void
  orientation?: 'vertical' | 'horizontal'
  /** 'pill' (default) is the sliding-indicator pill group used by filter
   * bars. 'folder' renders manila-folder-style tabs — flush against the
   * panel below them, with the active tab visually fused to the panel's
   * top edge — for sibling sections (e.g. Categories/Buckets) that read
   * as separate pages rather than a segmented control. */
  variant?: 'pill' | 'folder'
  ariaLabel: string
}

/** Controlled tab list — same active-state visual language as
 * Layout's sidebar NavLink (raised tile background, semibold ink
 * text) but as a `role=tablist` with an animated sliding indicator
 * and arrow-key navigation, since no tabs primitive existed before
 * Categories needed a Categories/Buckets split. */
export function Tabs({
  items,
  activeKey,
  onChange,
  orientation = 'horizontal',
  variant = 'pill',
  ariaLabel,
}: TabsProps) {
  const refs = useRef<Map<string, HTMLButtonElement>>(new Map())

  const activeIndex = Math.max(0, items.findIndex((item) => item.key === activeKey))

  const focusAndSelect = (index: number) => {
    const item = items[index]
    if (!item) return
    onChange(item.key)
    refs.current.get(item.key)?.focus()
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    const forward = orientation === 'vertical' ? 'ArrowDown' : 'ArrowRight'
    const backward = orientation === 'vertical' ? 'ArrowUp' : 'ArrowLeft'
    if (event.key === forward) {
      event.preventDefault()
      focusAndSelect((activeIndex + 1) % items.length)
    } else if (event.key === backward) {
      event.preventDefault()
      focusAndSelect((activeIndex - 1 + items.length) % items.length)
    } else if (event.key === 'Home') {
      event.preventDefault()
      focusAndSelect(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      focusAndSelect(items.length - 1)
    }
  }

  const listClassName = [
    styles.list,
    orientation === 'vertical' ? styles.listVertical : null,
    variant === 'folder' ? styles.listFolder : null,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={listClassName}
      role="tablist"
      aria-label={ariaLabel}
      aria-orientation={orientation}
      onKeyDown={handleKeyDown}
    >
      {variant === 'pill' && (
        <div
          className={styles.indicator}
          style={
            orientation === 'vertical'
              ? { transform: `translateY(${activeIndex * 100}%)`, height: `${100 / items.length}%`, width: undefined }
              : { transform: `translateX(${activeIndex * 100}%)`, width: `${100 / items.length}%` }
          }
          aria-hidden="true"
        />
      )}
      {items.map((item) => {
        const isActive = item.key === activeKey
        return (
          <button
            key={item.key}
            ref={(el) => {
              if (el) refs.current.set(item.key, el)
              else refs.current.delete(item.key)
            }}
            type="button"
            role="tab"
            id={`tab-${item.key}`}
            aria-selected={isActive}
            aria-controls={`tabpanel-${item.key}`}
            tabIndex={isActive ? 0 : -1}
            className={isActive ? `${styles.tab} ${styles.tabActive}` : styles.tab}
            onClick={() => onChange(item.key)}
          >
            {item.label}
          </button>
        )
      })}
    </div>
  )
}

export function TabPanel({
  tabKey,
  children,
}: {
  tabKey: string
  children: React.ReactNode
}) {
  return (
    <div role="tabpanel" id={`tabpanel-${tabKey}`} aria-labelledby={`tab-${tabKey}`}>
      {children}
    </div>
  )
}
