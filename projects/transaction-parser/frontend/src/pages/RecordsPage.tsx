import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { ApiError } from '../api/client'
import { usePatchTransaction } from '../api/hooks/usePatchTransaction'
import { useMonths, useTransactions } from '../api/hooks/useTransactions'
import type { MonthOption, SortOrder, TransactionSortField } from '../api/types'
import { AddKeywordDialog } from '../components/CategoryPicker/AddKeywordDialog'
import { NewCategoryDialog } from '../components/CategoryPicker/NewCategoryDialog'
import type { RecategorizedInfo } from '../components/CategoryPicker/CategoryPicker'
import { BulkSortDialog } from '../components/BulkSortDialog/BulkSortDialog'
import { FilterBar, initialFilterState, type RecordsFilterState } from '../components/FilterBar/FilterBar'
import { SearchInput } from '../components/FilterBar/SearchInput'
import { TransactionsTable } from '../components/TransactionsTable/TransactionsTable'
import styles from './RecordsPage.module.css'

const PAGE_SIZE = 50

/** A custom date range takes priority verbatim (it's mutually
 * exclusive with month chips at the FilterBar level, so the two are
 * never both populated — but this order still matters if that
 * invariant is ever relaxed). */
function deriveDateRange(
  filters: Pick<RecordsFilterState, 'monthKeys' | 'dateRange'>,
  options: MonthOption[],
): { date_from?: string; date_to?: string } {
  if (filters.dateRange) return { date_from: filters.dateRange.from, date_to: filters.dateRange.to }
  if (filters.monthKeys.length === 0) return {}
  const selected = options.filter((option) => filters.monthKeys.includes(option.key))
  if (selected.length === 0) return {}
  const from = selected.reduce((min, o) => (o.from < min ? o.from : min), selected[0]!.from)
  const to = selected.reduce((max, o) => (o.to > max ? o.to : max), selected[0]!.to)
  return { date_from: from, date_to: to }
}

interface PendingKeyword {
  transactionId: number
  description: string
  categoryId: number
  categoryName: string
}

interface PendingNewCategory {
  transactionId: number
  description: string
}

export function RecordsPage() {
  const [filters, setFilters] = usePreference<RecordsFilterState>('filters:records', initialFilterState)
  const [sort, setSort] = useState<TransactionSortField>('txn_date')
  const [order, setOrder] = useState<SortOrder>('desc')
  const [page, setPage] = useState(0)
  const [pendingKeyword, setPendingKeyword] = useState<PendingKeyword | null>(null)
  const [pendingNewCategory, setPendingNewCategory] = useState<PendingNewCategory | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [showBulkSort, setShowBulkSort] = useState(false)
  const { data: months } = useMonths()
  const patchTransaction = usePatchTransaction()

  const dateRange = useMemo(
    () => deriveDateRange(filters, months ?? []),
    [filters, months],
  )

  const queryFilters = useMemo(
    () => ({
      date_from: dateRange.date_from,
      date_to: dateRange.date_to,
      account_ids: filters.accountIds.length ? filters.accountIds : undefined,
      category_ids: filters.categoryIds.length ? filters.categoryIds : undefined,
      q: filters.search || undefined,
      recurring_only: filters.recurringOnly || undefined,
      include_excluded: filters.includeExcluded,
      sort,
      order,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    }),
    [dateRange, filters, sort, order, page],
  )

  const { data, isLoading, isError, error } = useTransactions(queryFilters)

  // Changing a filter re-queries the same scroll position — only the
  // page NUMBER resets (a stale offset against a newer, smaller result
  // set would otherwise paginate past the end), the viewport does not
  // jump anywhere on its own. The row selection is cleared on every
  // filter/sort/page change too — it's scoped to "whatever's on screen
  // right now," not meant to survive the underlying result set shifting
  // out from under it.
  const handleFilterChange = (next: RecordsFilterState) => {
    setFilters(next)
    setPage(0)
    setSelectedIds(new Set())
  }

  const handleSortChange = (field: TransactionSortField) => {
    if (field === sort) {
      setOrder((current) => (current === 'asc' ? 'desc' : 'asc'))
    } else {
      setSort(field)
      setOrder('desc')
    }
    setPage(0)
    setSelectedIds(new Set())
  }

  const handlePageChange = (next: number) => {
    setPage(next)
    setSelectedIds(new Set())
  }

  const toggleSelect = (id: number) => {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    const pageIds = (data?.items ?? []).map((t) => t.id)
    const allSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id))
    setSelectedIds((current) => {
      const next = new Set(current)
      if (allSelected) {
        for (const id of pageIds) next.delete(id)
      } else {
        for (const id of pageIds) next.add(id)
      }
      return next
    })
  }

  const total = data?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const handleRecategorized = (transactionId: number, description: string, info: RecategorizedInfo) => {
    // "Uncategorized" is the only target where a keyword prompt makes
    // no sense — every other category (including system ones like
    // "Payments & Transfers") should still offer to learn a keyword.
    if (info.categoryName === 'Uncategorized') return
    setPendingKeyword({
      transactionId,
      description,
      categoryId: info.categoryId,
      categoryName: info.categoryName,
    })
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Records</h1>
      </header>

      <FilterBar
        filters={filters}
        onChange={handleFilterChange}
        totalCount={data?.total}
        isLoading={isLoading}
        hideSearch
      />

      {isError && (
        <p className={styles.errorBanner}>
          {error instanceof ApiError ? error.message : 'Could not load transactions.'}
        </p>
      )}

      <div className={styles.searchRow}>
        <SearchInput
          value={filters.search}
          onChange={(search) => handleFilterChange({ ...filters, search })}
        />
      </div>

      <TransactionsTable
        transactions={data?.items ?? []}
        sort={sort}
        order={order}
        onSortChange={handleSortChange}
        page={page}
        pageCount={pageCount}
        onPageChange={handlePageChange}
        total={total}
        pageSize={PAGE_SIZE}
        onRecategorized={handleRecategorized}
        onRequestNewCategory={(transactionId, description) =>
          setPendingNewCategory({ transactionId, description })
        }
        selectedIds={selectedIds}
        onToggleSelect={toggleSelect}
        onToggleSelectAll={toggleSelectAll}
        onBulkSort={() => setShowBulkSort(true)}
        onClearSelection={() => setSelectedIds(new Set())}
      />

      {pendingKeyword && (
        <AddKeywordDialog
          categoryId={pendingKeyword.categoryId}
          categoryName={pendingKeyword.categoryName}
          description={pendingKeyword.description}
          onDone={() => setPendingKeyword(null)}
        />
      )}

      {showBulkSort && (
        <BulkSortDialog
          transactionIds={[...selectedIds]}
          onClose={() => setShowBulkSort(false)}
          onDone={() => {
            setShowBulkSort(false)
            setSelectedIds(new Set())
          }}
        />
      )}

      {pendingNewCategory && (
        <NewCategoryDialog
          description={pendingNewCategory.description}
          onCancel={() => setPendingNewCategory(null)}
          onCreated={(category) => {
            const { transactionId, description } = pendingNewCategory
            setPendingNewCategory(null)
            // Apply the new category to the transaction that requested
            // it, same as CategoryPicker's own select-change path would
            // — then offer the keyword follow-up for it, using the
            // category object the create mutation just returned (not a
            // lookup into the categories list, which hasn't refetched
            // yet and wouldn't contain this brand-new category).
            patchTransaction.mutate(
              { id: transactionId, patch: { category_id: category.id } },
              {
                onSuccess: () =>
                  setPendingKeyword({
                    transactionId,
                    description,
                    categoryId: category.id,
                    categoryName: category.name,
                  }),
              },
            )
          }}
        />
      )}
    </div>
  )
}
