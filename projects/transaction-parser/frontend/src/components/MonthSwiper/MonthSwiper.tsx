import { useRef, useState } from 'react'
import styles from './MonthSwiper.module.css'

interface MonthSwiperProps {
  label: string
  canGoNewer: boolean
  canGoOlder: boolean
  /** Small caption under the label — e.g. "All records" / "Current
   * month". Omit for no caption. */
  badge?: string
  onNewer: () => void
  onOlder: () => void
}

const SWIPE_THRESHOLD_PX = 50

/** The Overview/Time-Series/Distribution scope header: title + prev/
 * next, plus touch-swipe (left = older, right = newer) over the same
 * header area so swiping works on touch devices without fighting
 * Recharts' own pointer handling on the chart itself. Generalized
 * from a Time-Series-only "latest month" control to a three-page
 * shared "All → newest → older" scope swiper — `isLatest` is gone in
 * favor of `canGoNewer` since "newer than the newest month" is now
 * "All", not a disabled state. */
export function MonthSwiper({ label, canGoNewer, canGoOlder, badge, onNewer, onOlder }: MonthSwiperProps) {
  const touchStartX = useRef<number | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0]?.clientX ?? null
    setDragging(true)
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    setDragging(false)
    if (touchStartX.current === null) return
    const endX = e.changedTouches[0]?.clientX ?? touchStartX.current
    const delta = endX - touchStartX.current
    touchStartX.current = null
    if (Math.abs(delta) < SWIPE_THRESHOLD_PX) return
    if (delta > 0 && canGoNewer) onNewer()
    if (delta < 0 && canGoOlder) onOlder()
  }

  return (
    <div
      className={dragging ? `${styles.swiper} ${styles.swiperDragging}` : styles.swiper}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <button
        type="button"
        className={styles.navButton}
        onClick={onOlder}
        disabled={!canGoOlder}
        aria-label="Older"
      >
        ‹
      </button>
      <div className={styles.labelWrap}>
        {/* No content-based `key` here: this is a single static child
         * in a fixed slot, not a list item, so React updates its text
         * in place correctly without one. Keying by `label`/`badge`
         * text (removed) was meant to retrigger the CSS crossfade on
         * every change, but a content key isn't guaranteed unique
         * across a transition (e.g. "Month view" -> "Month view" when
         * only the month label changes) and could leave a stale node
         * mounted alongside the new one — surfacing as a duplicate
         * "All records" label and a React "two children with the
         * same key" warning. */}
        <span className={styles.label}>{label}</span>
        {badge && <span className={styles.latestBadge}>{badge}</span>}
      </div>
      <button
        type="button"
        className={styles.navButton}
        onClick={onNewer}
        disabled={!canGoNewer}
        aria-label="Newer"
      >
        ›
      </button>
    </div>
  )
}
