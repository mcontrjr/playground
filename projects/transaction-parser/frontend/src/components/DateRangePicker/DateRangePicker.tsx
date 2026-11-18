import { useEffect, useRef, useState } from 'react'
import styles from './DateRangePicker.module.css'

export interface DateRange {
  from: string // ISO date
  to: string // ISO date
}

interface DateRangePickerProps {
  value?: DateRange
  onChange: (range: DateRange) => void
  onClear: () => void
}

const DISPLAY_FORMATTER = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
const WEEKDAY_LABELS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

function toIso(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseIso(iso: string): Date {
  return new Date(`${iso}T00:00:00`)
}

function formatDisplay(range: DateRange): string {
  return `${DISPLAY_FORMATTER.format(parseIso(range.from))} – ${DISPLAY_FORMATTER.format(parseIso(range.to))}`
}

function buildMonthGrid(viewDate: Date): (Date | null)[] {
  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()
  const firstOfMonth = new Date(year, month, 1)
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const leadingBlanks = firstOfMonth.getDay()
  const cells: (Date | null)[] = []
  for (let i = 0; i < leadingBlanks; i += 1) cells.push(null)
  for (let d = 1; d <= daysInMonth; d += 1) cells.push(new Date(year, month, d))
  return cells
}

/** Hand-rolled date-range popover (no dependency) for the Records
 * page's month filter row: a chip trigger styled like the other
 * FilterChipGroup pills, an anchored popover with a single month grid
 * and ‹ › nav, click-start-then-end selection (swapping if the second
 * click lands before the first), and Clear/Apply actions. */
export function DateRangePicker({ value, onChange, onClear }: DateRangePickerProps) {
  const [open, setOpen] = useState(false)
  const [viewDate, setViewDate] = useState(() => parseIso(value?.from ?? toIso(new Date())))
  const [draftStart, setDraftStart] = useState<string | null>(value?.from ?? null)
  const [draftEnd, setDraftEnd] = useState<string | null>(value?.to ?? null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handleClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('mousedown', handleClick)
    window.addEventListener('keydown', handleKey)
    return () => {
      window.removeEventListener('mousedown', handleClick)
      window.removeEventListener('keydown', handleKey)
    }
  }, [open])

  const openPopover = () => {
    setDraftStart(value?.from ?? null)
    setDraftEnd(value?.to ?? null)
    setViewDate(parseIso(value?.from ?? toIso(new Date())))
    setOpen(true)
  }

  const handleDayClick = (iso: string) => {
    if (!draftStart || (draftStart && draftEnd)) {
      setDraftStart(iso)
      setDraftEnd(null)
      return
    }
    // Second click: order start/end regardless of click order.
    if (iso < draftStart) {
      setDraftEnd(draftStart)
      setDraftStart(iso)
    } else {
      setDraftEnd(iso)
    }
  }

  const apply = () => {
    if (draftStart && draftEnd) {
      onChange({ from: draftStart, to: draftEnd })
      setOpen(false)
    }
  }

  const clear = () => {
    setDraftStart(null)
    setDraftEnd(null)
    onClear()
    setOpen(false)
  }

  const cells = buildMonthGrid(viewDate)
  const monthLabel = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(viewDate)

  const inRange = (iso: string) => {
    if (!draftStart) return false
    const end = draftEnd ?? draftStart
    const lo = draftStart < end ? draftStart : end
    const hi = draftStart < end ? end : draftStart
    return iso >= lo && iso <= hi
  }

  return (
    <div className={styles.container} ref={containerRef}>
      <button
        type="button"
        className={value ? `${styles.trigger} ${styles.triggerActive}` : styles.trigger}
        onClick={() => (open ? setOpen(false) : openPopover())}
        aria-expanded={open}
        data-testid="date-range-trigger"
      >
        {value ? formatDisplay(value) : 'Date range'}
      </button>

      {open && (
        <div className={styles.popover} role="dialog" aria-label="Pick a date range">
          <div className={styles.nav}>
            <button
              type="button"
              className={styles.navButton}
              aria-label="Previous month"
              onClick={() => setViewDate((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1))}
            >
              ‹
            </button>
            <span className={styles.monthLabel}>{monthLabel}</span>
            <button
              type="button"
              className={styles.navButton}
              aria-label="Next month"
              onClick={() => setViewDate((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1))}
            >
              ›
            </button>
          </div>

          <div className={styles.weekdays}>
            {WEEKDAY_LABELS.map((w) => (
              <span key={w} className={styles.weekday}>
                {w}
              </span>
            ))}
          </div>

          <div className={styles.grid}>
            {cells.map((date, i) => {
              if (!date) return <span key={`blank-${i}`} className={styles.dayBlank} />
              const iso = toIso(date)
              const isStart = iso === draftStart
              const isEnd = iso === draftEnd
              const selected = isStart || isEnd
              const inside = inRange(iso)
              return (
                <button
                  key={iso}
                  type="button"
                  className={[
                    styles.day,
                    inside ? styles.dayInRange : '',
                    selected ? styles.daySelected : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => handleDayClick(iso)}
                >
                  {date.getDate()}
                </button>
              )
            })}
          </div>

          <div className={styles.actions}>
            <button type="button" className={styles.clearButton} onClick={clear}>
              Clear
            </button>
            <button
              type="button"
              className={styles.applyButton}
              disabled={!draftStart || !draftEnd}
              onClick={apply}
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
