import { Fragment } from 'react'
import type { CategorySource, Transaction } from '../../api/types'
import { Modal } from '../Modal/Modal'
import styles from './TransactionDetailModal.module.css'

const MONEY_FORMATTER = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

/** How this row's category was decided. A detail view is the right
 * place for the precise value rather than a coarse matched/manual
 * split, so each source keeps its own wording — 'transfer' in
 * particular is worth distinguishing, since those are matched before
 * category priority is consulted at all. */
const SOURCE_LABELS: Record<CategorySource, string> = {
  keyword: 'Matched a keyword',
  transfer: 'Matched a transfer keyword',
  default: 'No rule matched',
  manual: 'Set by hand',
  bulk: 'Set by hand (bulk)',
}

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
          <dt>Source</dt>
          <dd data-testid="detail-source">{SOURCE_LABELS[txn.category_source] ?? txn.category_source}</dd>
          {txn.matched_keyword && (
            <>
              <dt>Matched on</dt>
              <dd>
                <code className={styles.keyword} data-testid="detail-matched-keyword">
                  {txn.matched_keyword}
                </code>
              </dd>
            </>
          )}
          <dt>Recurring</dt>
          <dd data-testid="detail-recurring">
            {txn.is_recurring ? (txn.recurrence === 'yearly' ? 'Yearly' : 'Monthly') : 'One-off'}
          </dd>
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
