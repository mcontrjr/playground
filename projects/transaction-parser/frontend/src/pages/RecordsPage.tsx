import { useMemo, useState } from 'react'
import { usePreference } from '../api/hooks/usePreference'
import { ApiError } from '../api/client'
import { usePatchTransaction } from '../api/hooks/usePatchTransaction'
import { useMonths, useTransactions } from '../api/hooks/useTransactions'
import type { MonthOption, SortOrder, TransactionSortField } from '../api/types'
import { AddKeywordDialog } from '../components/CategoryPicker/AddKeywordDialog'
import { NewCategoryDialog } from '../components/CategoryPicker/NewCategoryDialog'
import type { RecategorizedInfo } from '../components/CategoryPicker/CategoryPicker'
import { FilterBar, initialFilterState, type RecordsFilterState } from '../components/FilterBar/FilterBar'
import { TransactionsTable } from '../components/TransactionsTable/TransactionsTable'
import styles from './RecordsPage.module.css'

const PAGE_SIZE = 50

function deriveDateRange(
  monthKeys: string[],
  options: MonthOption[],
): { date_from?: string; date_to?: string } {
  if (monthKeys.length === 0) return {}
  const selected = options.filter((option) => monthKeys.includes(option.key))
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
  const { data: months } = useMonths()
  const patchTransaction = usePatchTransaction()

  const dateRange = useMemo(
    () => deriveDateRange(filters.monthKeys, months ?? []),
    [filters.monthKeys, months],
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
  // jump anywhere on its own.
  const handleFilterChange = (next: RecordsFilterState) => {
    setFilters(next)
    setPage(0)
  }

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

  const handleRecategorized = (transactionId: number, description: string, info: RecategorizedInfo) => {
    if (info.isSystem) return
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
      />

      {isError && (
        <p className={styles.errorBanner}>
          {error instanceof ApiError ? error.message : 'Could not load transactions.'}
        </p>
      )}

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
        onRecategorized={handleRecategorized}
        onRequestNewCategory={(transactionId, description) =>
          setPendingNewCategory({ transactionId, description })
        }
      />

      {pendingKeyword && (
        <AddKeywordDialog
          categoryId={pendingKeyword.categoryId}
          categoryName={pendingKeyword.categoryName}
          description={pendingKeyword.description}
          onDone={() => setPendingKeyword(null)}
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
