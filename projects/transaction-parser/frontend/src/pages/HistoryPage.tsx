import { useState } from 'react'
import { useAuditEvents } from '../api/hooks/useAuditEvents'
import type { AuditEvent } from '../api/types'
import styles from './HistoryPage.module.css'

const PAGE_SIZE = 25

const ABSOLUTE_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

function formatRelative(iso: string): string {
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diffSeconds = Math.round((now - then) / 1000)
  if (diffSeconds < 60) return 'just now'
  const diffMinutes = Math.round(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.round(diffHours / 24)
  return `${diffDays}d ago`
}

function EventRow({ event }: { event: AuditEvent }) {
  return (
    <div className={styles.row} data-testid="audit-row" data-event-type={event.event_type}>
      <span className={styles.pill}>{event.event_type}</span>
      <span className={styles.description}>{event.description}</span>
      {event.affected_count != null && (
        <span className={styles.countBadge}>
          {event.affected_count} record{event.affected_count === 1 ? '' : 's'}
        </span>
      )}
      <span className={styles.timestamp} title={ABSOLUTE_FORMATTER.format(new Date(event.created_at))}>
        {formatRelative(event.created_at)}
      </span>
    </div>
  )
}

/** Audit trail — flat reverse-chronological feed of every mutation
 * the backend instruments (bucket/category/keyword changes,
 * transaction recategorizations), paginated by offset since the
 * total count is cheap and "Load more" reads more naturally here
 * than page numbers for a feed people skim top-down. */
export function HistoryPage() {
  const [limit, setLimit] = useState(PAGE_SIZE)
  const { data, isLoading } = useAuditEvents({ limit, offset: 0 })

  const items = data?.items ?? []
  const hasMore = data ? items.length < data.total : false

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>History</h1>
        <p className={styles.subtitle}>
          Every bucket, category, keyword, and recategorization change — newest first.
        </p>
      </header>

      {isLoading ? (
        <p className={styles.empty}>Loading…</p>
      ) : items.length === 0 ? (
        <p className={styles.empty}>No changes recorded yet.</p>
      ) : (
        <div className={styles.list}>
          {items.map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </div>
      )}

      {hasMore && (
        <button
          type="button"
          className={styles.loadMoreButton}
          onClick={() => setLimit((l) => l + PAGE_SIZE)}
          data-testid="history-load-more"
        >
          Load more
        </button>
      )}
    </div>
  )
}
