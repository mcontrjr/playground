import type { BatchSummary } from '../../api/types'
import styles from './BatchList.module.css'

interface BatchListProps {
  batches: BatchSummary[]
}

const STATUS_CLASS: Record<BatchSummary['status'], string> = {
  completed: styles.statusCompleted,
  completed_with_errors: styles.statusPartial,
  failed: styles.statusFailed,
}

const STATUS_LABEL: Record<BatchSummary['status'], string> = {
  completed: 'Completed',
  completed_with_errors: 'Completed with errors',
  failed: 'Failed',
}

const DATE_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

export function BatchList({ batches }: BatchListProps) {
  if (batches.length === 0) {
    return <p className={styles.empty}>No uploads yet.</p>
  }

  return (
    <ul className={styles.list} data-testid="batch-list">
      {batches.map((batch) => (
        <li key={batch.id} className={styles.row} data-testid="batch-row" data-filename={batch.filename}>
          <div>
            <div className={styles.filename}>{batch.filename}</div>
            <div className={styles.institution}>{batch.institution}</div>
          </div>
          <span className={styles.counts}>
            {batch.counts.inserted} inserted &middot; {batch.counts.duplicates} dup &middot;{' '}
            {batch.counts.failures} failed
          </span>
          <span className={STATUS_CLASS[batch.status]}>{STATUS_LABEL[batch.status]}</span>
          <span className={styles.counts}>{DATE_FORMATTER.format(new Date(batch.created_at))}</span>
        </li>
      ))}
    </ul>
  )
}
