import { useState } from 'react'
import { useTransactions } from '../../api/hooks/useTransactions'
import type { SortOrder, TransactionFilters, TransactionSortField } from '../../api/types'
import { TransactionsTable } from '../TransactionsTable/TransactionsTable'
import styles from './RecordsPanel.module.css'

interface RecordsPanelProps {
  title: string
  filters: TransactionFilters
  onClose: () => void
}

const PAGE_SIZE = 25

/** The records drill-down used by Time Series (day/month bar or line
 * click) and Distribution (category click): an expand/collapse panel
 * that mounts `useTransactions` + the existing `TransactionsTable`
 * scoped to whatever filters the caller passes. Expand/collapse
 * animates via `grid-template-rows: 0fr -> 1fr` (not height:auto,
 * which can't be transitioned) on the wrapper — the panel itself is
 * always mounted so the very first expand still animates instead of
 * popping in. */
export function RecordsPanel({ title, filters, onClose }: RecordsPanelProps) {
  const [sort, setSort] = useState<TransactionSortField>('txn_date')
  const [order, setOrder] = useState<SortOrder>('desc')
  const [page, setPage] = useState(0)

  const { data, isLoading } = useTransactions({
    ...filters,
    sort,
    order,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  })

  const handleSortChange = (field: TransactionSortField) => {
    if (field === sort) {
      setOrder((current) => (current === 'asc' ? 'desc' : 'asc'))
    } else {
      setSort(field)
      setOrder('desc')
    }
    setPage(0)
  }

  const total = data?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className={styles.expander} data-testid="records-panel">
      <div className={styles.inner}>
        <div className={styles.panel}>
          <div className={styles.header}>
            <h3 className={styles.title}>{title}</h3>
            <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close records panel">
              Close ✕
            </button>
          </div>

          {isLoading ? (
            <p className={styles.loading}>Loading…</p>
          ) : (
            <TransactionsTable
              transactions={data?.items ?? []}
              sort={sort}
              order={order}
              onSortChange={handleSortChange}
              page={page}
              pageCount={pageCount}
              onPageChange={setPage}
              total={total}
              pageSize={PAGE_SIZE}
              onRecategorized={() => {}}
              onRequestNewCategory={() => {}}
            />
          )}
        </div>
      </div>
    </div>
  )
}
