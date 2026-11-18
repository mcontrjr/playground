import { useState } from 'react'
import { usePatchTransaction } from '../../api/hooks/usePatchTransaction'
import type { SortOrder, Transaction, TransactionSortField } from '../../api/types'
import { CategoryPicker, type RecategorizedInfo } from '../CategoryPicker/CategoryPicker'
import { TransactionDetailModal } from './TransactionDetailModal'
import styles from './TransactionsTable.module.css'

interface Column {
  field: TransactionSortField
  label: string
}

const COLUMNS: Column[] = [
  { field: 'txn_date', label: 'Date' },
  { field: 'description', label: 'Description' },
  { field: 'category', label: 'Category' },
  { field: 'amount', label: 'Amount' },
]

interface TransactionsTableProps {
  transactions: Transaction[]
  sort: TransactionSortField
  order: SortOrder
  onSortChange: (field: TransactionSortField) => void
  page: number
  pageCount: number
  onPageChange: (page: number) => void
  total: number
  pageSize: number
  onRecategorized: (transactionId: number, description: string, info: RecategorizedInfo) => void
  onRequestNewCategory: (transactionId: number, description: string) => void
}

const DATE_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

const MONEY_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatAmount(amount: string): string {
  const value = Number.parseFloat(amount)
  const formatted = MONEY_FORMATTER.format(Math.abs(value))
  return value < 0 ? `−${formatted}` : formatted
}

function formatDate(isoDate: string): string {
  return DATE_FORMATTER.format(new Date(`${isoDate}T00:00:00`))
}

/** Cycles none -> monthly -> yearly -> none. Independent of
 * categorization: a transaction's recurrence flag is its own axis
 * ("is this a recurring bill/subscription?"), surfaced here so it can
 * be set right from Records without a separate screen. */
function RecurringToggle({ txn }: { txn: Transaction }) {
  const patchTransaction = usePatchTransaction()

  const next = txn.is_recurring
    ? txn.recurrence === 'monthly'
      ? { is_recurring: true, recurrence: 'yearly' as const }
      : { is_recurring: false, recurrence: null }
    : { is_recurring: true, recurrence: 'monthly' as const }

  const label = txn.is_recurring ? (txn.recurrence === 'yearly' ? 'Yearly' : 'Monthly') : 'One-off'

  return (
    <button
      type="button"
      className={txn.is_recurring ? `${styles.recurringToggle} ${styles.recurringActive}` : styles.recurringToggle}
      onClick={() => patchTransaction.mutate({ id: txn.id, patch: next })}
      disabled={patchTransaction.isPending}
      title="Click to cycle: one-off → monthly → yearly"
      data-testid="recurring-toggle"
    >
      {label}
    </button>
  )
}

export function TransactionsTable({
  transactions,
  sort,
  order,
  onSortChange,
  page,
  pageCount,
  onPageChange,
  total,
  pageSize,
  onRecategorized,
  onRequestNewCategory,
}: TransactionsTableProps) {
  const rangeStart = page * pageSize + 1
  const rangeEnd = Math.min(total, (page + 1) * pageSize)
  const [detailTxn, setDetailTxn] = useState<Transaction | null>(null)

  // The table shell (header, pagination) stays mounted even with zero
  // rows, so switching filters to a narrower result never collapses
  // the page's height down to one centered line and back — that
  // height swing is what reads as "the page jumping" on a filter
  // change, independent of any actual scroll-position reset.
  return (
    <div>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {COLUMNS.map((column) => (
                <th key={column.field} className={column.field === 'amount' ? styles.colAmount : undefined}>
                  <button
                    type="button"
                    className={styles.sortButton}
                    onClick={() => onSortChange(column.field)}
                  >
                    {column.label}
                    {sort === column.field && (
                      <span className={styles.sortArrow}>{order === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
              ))}
              <th>
                <span className="label-caps">Account</span>
              </th>
              <th>
                <span className="label-caps">Recurring</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 2} className={styles.empty}>
                  No transactions match these filters.
                </td>
              </tr>
            )}
            {transactions.map((txn) => {
              const value = Number.parseFloat(txn.amount)
              return (
                <tr key={txn.id} data-testid="transaction-row" data-description={txn.description}>
                  <td className={styles.clickable} onClick={() => setDetailTxn(txn)}>
                    {formatDate(txn.txn_date)}
                  </td>
                  <td
                    className={`${styles.description} ${styles.clickable}`}
                    title={txn.description}
                    onClick={() => setDetailTxn(txn)}
                  >
                    {txn.description}
                  </td>
                  <td>
                    <CategoryPicker
                      transactionId={txn.id}
                      categoryId={txn.category_id}
                      onRecategorized={(info) => onRecategorized(txn.id, txn.description, info)}
                      onRequestNewCategory={() => onRequestNewCategory(txn.id, txn.description)}
                    />
                  </td>
                  <td
                    className={`${styles.colAmount} ${styles.amount} ${styles.clickable} ${
                      value < 0 ? styles.amountNegative : styles.amountPositive
                    }`}
                    data-testid="transaction-amount"
                    onClick={() => setDetailTxn(txn)}
                  >
                    {formatAmount(txn.amount)}
                  </td>
                  <td className={`${styles.muted} ${styles.clickable}`} onClick={() => setDetailTxn(txn)}>
                    {txn.account_name}
                  </td>
                  <td>
                    <RecurringToggle txn={txn} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <span>
          {rangeStart}&ndash;{rangeEnd} of {total}
        </span>
        <div className={styles.pageButtons}>
          <button
            type="button"
            className={styles.pageButton}
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 0}
          >
            Previous
          </button>
          <button
            type="button"
            className={styles.pageButton}
            onClick={() => onPageChange(page + 1)}
            disabled={page + 1 >= pageCount}
          >
            Next
          </button>
        </div>
      </div>

      {detailTxn && <TransactionDetailModal txn={detailTxn} onClose={() => setDetailTxn(null)} />}
    </div>
  )
}
