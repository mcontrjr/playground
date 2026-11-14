import { useRef, useState } from 'react'
import styles from './MonthSwiper.module.css'

interface MonthSwiperProps {
  label: string
  isLatest: boolean
  canGoOlder: boolean
  onNewer: () => void
  onOlder: () => void
}

const SWIPE_THRESHOLD_PX = 50

/** The Time Series month header: title + prev/next, plus touch-swipe
 * (left = older, right = newer) over the same header area so the
 * "the graph will swipe for the other months" requirement works on
 * touch devices without needing a drag gesture on the chart itself
 * (which would fight with Recharts' own pointer handling). */
export function MonthSwiper({ label, isLatest, canGoOlder, onNewer, onOlder }: MonthSwiperProps) {
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
    if (delta > 0 && !isLatest) onNewer()
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
        aria-label="Previous month"
      >
        ‹
      </button>
      <div className={styles.labelWrap}>
        <span className={styles.label}>{label}</span>
        {isLatest && <span className={styles.latestBadge}>Current month</span>}
      </div>
      <button
        type="button"
        className={styles.navButton}
        onClick={onNewer}
        disabled={isLatest}
        aria-label="Next month"
      >
        ›
      </button>
    </div>
  )
}
