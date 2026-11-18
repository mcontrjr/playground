import { useEffect, useRef, useState } from 'react'
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
  /** Bulk-sort selection UI (row checkboxes, select-all, the action
   * bar) only renders when all of these are provided — omitted by
   * read-only embeds like RecordsPanel's drill-down, which has no
   * page-level selection state to back it. */
  selectedIds?: Set<number>
  onToggleSelect?: (id: number) => void
  onToggleSelectAll?: () => void
  onBulkSort?: () => void
  onClearSelection?: () => void
}

/** Tri-state header checkbox: unchecked when nothing on this page is
 * selected, checked when every row is, indeterminate in between —
 * `indeterminate` is a DOM-only property with no JSX/HTML attribute
 * equivalent, so it has to be set imperatively via a ref. */
function SelectAllCheckbox({
  transactions,
  selectedIds,
  onToggleSelectAll,
}: {
  transactions: Transaction[]
  selectedIds: Set<number>
  onToggleSelectAll: () => void
}) {
  const ref = useRef<HTMLInputElement>(null)
  const selectedOnPage = transactions.filter((t) => selectedIds.has(t.id)).length
  const allSelected = transactions.length > 0 && selectedOnPage === transactions.length
  const indeterminate = selectedOnPage > 0 && !allSelected

  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate
  }, [indeterminate])

  return (
    <input
      ref={ref}
      type="checkbox"
      className={styles.checkbox}
      checked={allSelected}
      onChange={onToggleSelectAll}
      aria-label="Select all on this page"
      data-testid="select-all-checkbox"
    />
  )
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
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onBulkSort,
  onClearSelection,
}: TransactionsTableProps) {
  const rangeStart = page * pageSize + 1
  const rangeEnd = Math.min(total, (page + 1) * pageSize)
  const [detailTxn, setDetailTxn] = useState<Transaction | null>(null)
  const selectionEnabled = selectedIds !== undefined && onToggleSelect && onToggleSelectAll

  // The table shell (header, pagination) stays mounted even with zero
  // rows, so switching filters to a narrower result never collapses
  // the page's height down to one centered line and back — that
  // height swing is what reads as "the page jumping" on a filter
  // change, independent of any actual scroll-position reset.
  return (
    <div>
      {selectionEnabled && selectedIds.size > 0 && (
        <div className={styles.selectionBar} data-testid="selection-bar">
          <span>
            <span className={styles.selectionCount}>{selectedIds.size}</span> selected
          </span>
          <button
            type="button"
            className={styles.bulkSortButton}
            onClick={onBulkSort}
            data-testid="open-bulk-sort"
          >
            Bulk sort
          </button>
          <button type="button" className={styles.clearSelectionButton} onClick={onClearSelection}>
            Clear selection
          </button>
        </div>
      )}

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {selectionEnabled && (
                <th className={styles.colCheckbox}>
                  <SelectAllCheckbox
                    transactions={transactions}
                    selectedIds={selectedIds}
                    onToggleSelectAll={onToggleSelectAll}
                  />
                </th>
              )}
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
                <td colSpan={COLUMNS.length + 2 + (selectionEnabled ? 1 : 0)} className={styles.empty}>
                  No transactions match these filters.
                </td>
              </tr>
            )}
            {transactions.map((txn) => {
              const value = Number.parseFloat(txn.amount)
              return (
                <tr key={txn.id} data-testid="transaction-row" data-description={txn.description}>
                  {selectionEnabled && (
                    <td>
                      <input
                        type="checkbox"
                        className={styles.checkbox}
                        checked={selectedIds.has(txn.id)}
                        onChange={() => onToggleSelect(txn.id)}
                        aria-label={`Select transaction: ${txn.description}`}
                        data-testid="row-checkbox"
                      />
                    </td>
                  )}
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
