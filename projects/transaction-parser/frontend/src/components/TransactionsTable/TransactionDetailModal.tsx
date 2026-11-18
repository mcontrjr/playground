import { Fragment } from 'react'
import type { Transaction } from '../../api/types'
import { Modal } from '../Modal/Modal'
import styles from './TransactionDetailModal.module.css'

const MONEY_FORMATTER = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

function formatAmount(amount: string): string {
  const value = Number.parseFloat(amount)
  const formatted = MONEY_FORMATTER.format(Math.abs(value))
  return value < 0 ? `−${formatted}` : formatted
}

/** Humanizes a raw_row column key for display, e.g. "CheckNumber" ->
 * "Check Number", "running_balance" -> "Running Balance" — the raw
 * keys are each bank's own CSV header text, so casing/separators vary
 * per institution_code and this normalizes them for a readable label
 * without needing a per-bank label map. */
function humanizeKey(key: string): string {
  const spaced = key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
  return spaced
    .split(' ')
    .filter(Boolean)
    .map((word) => word[0]!.toUpperCase() + word.slice(1))
    .join(' ')
}

/** Shows every field the originating bank's CSV actually had for this
 * row (raw_row), plus the parsed/derived fields — scoped to this one
 * transaction's institution_code, so a Schwab row never shows blank
 * Amex-only columns and vice versa. */
export function TransactionDetailModal({ txn, onClose }: { txn: Transaction; onClose: () => void }) {
  const rawEntries = Object.entries(txn.raw_row).filter(([, value]) => value !== '' && value != null)

  return (
    <Modal title="Transaction detail" onClose={onClose} ariaLabel="Transaction detail">
      <div className={styles.section}>
        <dl className={styles.grid}>
          <dt>Description</dt>
          <dd>{txn.description}</dd>
          <dt>Amount</dt>
          <dd className={Number(txn.amount) < 0 ? styles.negative : styles.positive}>
            {formatAmount(txn.amount)}
          </dd>
          <dt>Date</dt>
          <dd>{txn.txn_date}</dd>
          {txn.posted_date && (
            <>
              <dt>Posted</dt>
              <dd>{txn.posted_date}</dd>
            </>
          )}
          <dt>Account</dt>
          <dd>{txn.account_name}</dd>
          <dt>Category</dt>
          <dd>{txn.category_name ?? 'Uncategorized'}</dd>
          {txn.bank_category && (
            <>
              <dt>Bank category</dt>
              <dd>{txn.bank_category}</dd>
            </>
          )}
        </dl>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>
          {txn.institution_code.toUpperCase()} metadata
        </h3>
        {rawEntries.length > 0 ? (
          <dl className={styles.grid}>
            {rawEntries.map(([key, value]) => (
              <Fragment key={key}>
                <dt>{humanizeKey(key)}</dt>
                <dd>{value}</dd>
              </Fragment>
            ))}
          </dl>
        ) : (
          <p className={styles.empty}>No additional metadata for this source.</p>
        )}
      </div>

      <div className={styles.actions}>
        <button type="button" className={styles.closeButton} onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  )
}
