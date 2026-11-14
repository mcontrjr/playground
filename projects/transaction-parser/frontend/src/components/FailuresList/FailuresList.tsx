import { usePatchFailure } from '../../api/hooks/useFailures'
import type { ParseFailure } from '../../api/types'
import styles from './FailuresList.module.css'

interface FailuresListProps {
  failures: ParseFailure[]
}

export function FailuresList({ failures }: FailuresListProps) {
  const patchFailure = usePatchFailure()

  if (failures.length === 0) {
    return <p className={styles.empty}>No failures.</p>
  }

  return (
    <ul className={styles.list} data-testid="failures-list">
      {failures.map((failure) => (
        <li key={failure.id} className={styles.item} data-testid="failure-row">
          <span className={styles.lineNumber} data-testid="failure-line-number">
            #{failure.line_number}
          </span>
          <div className={styles.content}>
            <code className={styles.rawLine} data-testid="failure-raw-line">
              {failure.raw_line}
            </code>
            <span className={styles.errorMessage}>
              {failure.error_type}: {failure.error_message}
            </span>
          </div>
          {failure.resolved ? (
            <span className={styles.resolved} data-testid="failure-resolved">
              Resolved
            </span>
          ) : (
            <button
              type="button"
              className={styles.resolveButton}
              disabled={patchFailure.isPending}
              data-testid="failure-resolve-button"
              onClick={() =>
                patchFailure.mutate({ id: failure.id, patch: { resolved: true } })
              }
            >
              Mark resolved
            </button>
          )}
        </li>
      ))}
    </ul>
  )
}
