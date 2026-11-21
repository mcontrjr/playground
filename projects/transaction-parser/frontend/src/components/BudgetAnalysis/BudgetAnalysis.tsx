import { useMemo, useState } from 'react'
import { ApiError } from '../../api/client'
import { useAnalyticsDistribution } from '../../api/hooks/useAnalytics'
import { useCategories } from '../../api/hooks/useCategories'
import { usePatchTransaction } from '../../api/hooks/usePatchTransaction'
import { usePreference } from '../../api/hooks/usePreference'
import { useTransactionFacets, useTransactions } from '../../api/hooks/useTransactions'
import type {
  BudgetExpense,
  SortOrder,
  TransactionSortField,
} from '../../api/types'
import { AddKeywordDialog } from '../CategoryPicker/AddKeywordDialog'
import type { RecategorizedInfo } from '../CategoryPicker/CategoryPicker'
import { NewCategoryDialog } from '../CategoryPicker/NewCategoryDialog'
import { DonutChart } from '../charts/DonutChart'
import { formatCurrency, formatCurrencyPrecise, formatPercent } from '../charts/format'
import {
  assignDistributionColors,
  MAX_DISTRIBUTION_SLOTS,
  OTHER_LABEL,
} from '../charts/palette'
import { FilterBar, type RecordsFilterState } from '../FilterBar/FilterBar'
import { SearchInput } from '../FilterBar/SearchInput'
import { TransactionsTable } from '../TransactionsTable/TransactionsTable'
import styles from './BudgetAnalysis.module.css'

const PAGE_SIZE = 25
const LEADERBOARD_SIZE = 5

/** The unbudgeted analysis has its own filter state, but a narrower one
 * than Records: the month is fixed by the Budget page's MonthSwiper, so
 * there are no month chips or date-range picker here — only the
 * dimensions that make sense *within* one month's leftover spend. */
export interface BudgetAnalysisFilterState
  extends Pick<
    RecordsFilterState,
    'accountIds' | 'categoryIds' | 'search' | 'includeExcluded' | 'recurringOnly'
  > {}

export const initialAnalysisFilters: BudgetAnalysisFilterState = {
  accountIds: [],
  categoryIds: [],
  search: '',
  includeExcluded: false,
  recurringOnly: false,
}

interface BudgetAnalysisProps {
  /** The month the Budget page is currently showing, e.g. "October
   * 2026" — used in the section's prose. The month's actual *scope*
   * travels as dateFrom/dateTo. */
  monthLabel: string
  /** Every expense on this month's budget. Their linked categories are
   * what makes a transaction "accounted for"; everything else is what
   * this section breaks down. */
  expenses: BudgetExpense[]
  /** Inclusive bounds of the displayed month, already computed by the
   * page. */
  dateFrom: string
  dateTo: string
}

interface PendingKeyword {
  transactionId: number
  description: string
  categoryId: number
  categoryName: string
}

/** Pie slices for the leftover categories, folding everything past the
 * 12th into a single "Other" slice — same treatment as the Distribution
 * page, so the two charts read identically. */
function useUnbudgetedSlices(entries: { category_id: number | null; name: string; amount: string }[]) {
  return useMemo(() => {
    const sorted = [...entries].sort((a, b) => Number(b.amount) - Number(a.amount))
    const colors = assignDistributionColors(Math.min(sorted.length, MAX_DISTRIBUTION_SLOTS + 1))
    const kept = sorted.slice(0, MAX_DISTRIBUTION_SLOTS).map((entry, i) => ({
      key: String(entry.category_id),
      label: entry.name,
      value: Number(entry.amount),
      color: colors[i]!,
    }))
    if (sorted.length > MAX_DISTRIBUTION_SLOTS) {
      const rest = sorted.slice(MAX_DISTRIBUTION_SLOTS)
      kept.push({
        key: '__other__',
        label: OTHER_LABEL,
        value: rest.reduce((sum, e) => sum + Number(e.amount), 0),
        color: colors[MAX_DISTRIBUTION_SLOTS] ?? colors[MAX_DISTRIBUTION_SLOTS - 1]!,
      })
    }
    return kept
  }, [entries])
}

/** "Where the rest of it went" — the breakdown of everything in a month
 * that no budget expense claimed. Composed entirely from the pieces the
 * other pages already use (DonutChart + Distribution's legend rows,
 * FilterBar, TransactionsTable), laid out as a mosaic so the pie, the
 * biggest offenders, and the full record list are all visible at once.
 *
 * "Unbudgeted" is derived client-side as a set complement — the
 * categories linked to a budget expense, subtracted from all categories
 * — then pushed to the API as `exclude_category_ids` so the pie, the
 * leaderboard, and the table are all aggregated server-side against the
 * identical scope (and uncategorized spend, which an inclusive id list
 * could never match, stays in).
 */
export function BudgetAnalysis({ monthLabel, expenses, dateFrom, dateTo }: BudgetAnalysisProps) {
  const [filters, setFilters] = usePreference<BudgetAnalysisFilterState>(
    'filters:budget_analysis',
    initialAnalysisFilters,
  )
  const [sort, setSort] = useState<TransactionSortField>('txn_date')
  const [order, setOrder] = useState<SortOrder>('desc')
  const [page, setPage] = useState(0)
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const [pendingKeyword, setPendingKeyword] = useState<PendingKeyword | null>(null)
  const [pendingNewCategory, setPendingNewCategory] = useState<{
    transactionId: number
    description: string
  } | null>(null)

  const { data: categories } = useCategories()
  const patchTransaction = usePatchTransaction()

  const budgetedCategoryIds = useMemo(
    () => expenses.flatMap((expense) => expense.categories.map((c) => c.id)),
    [expenses],
  )

  /** The leftover categories, for the section's own category chips —
   * the full category list minus the budgeted ones. Without this the
   * FilterBar would offer chips for categories that can never match. */
  const unbudgetedCategories = useMemo(() => {
    const budgeted = new Set(budgetedCategoryIds)
    return (categories ?? []).filter((c) => !budgeted.has(c.id))
  }, [categories, budgetedCategoryIds])

  /** The fixed scope shared by all three views: this month, minus the
   * budgeted categories, under the account/transfers filters. */
  const analyticsScope = useMemo(
    () => ({
      date_from: dateFrom,
      date_to: dateTo,
      exclude_category_ids: budgetedCategoryIds.length ? budgetedCategoryIds : undefined,
      account_ids: filters.accountIds.length ? filters.accountIds : undefined,
      include_excluded: filters.includeExcluded,
    }),
    [dateFrom, dateTo, budgetedCategoryIds, filters.accountIds, filters.includeExcluded],
  )

  /** The same scope for transaction queries, plus `outflows_only`:
   * this section is about where *spending* landed, so the record list
   * and leaderboard are restricted to money out — the same set
   * /analytics/distribution sums. Without it a payroll deposit would
   * be listed as "unaccounted-for spend", since "Income" is excluded
   * from analytics but the transactions endpoint always lets it
   * through regardless of the transfers toggle. */
  const scope = useMemo(
    () => ({ ...analyticsScope, outflows_only: true }),
    [analyticsScope],
  )

  // The pie deliberately ignores the category/search/recurring filters:
  // it's the "at a glance" view of the whole leftover month, and the
  // table below is where you narrow down. Account + transfers scope DO
  // apply, since those change which money is yours to account for.
  const { data: distribution, isLoading: pieLoading } = useAnalyticsDistribution(analyticsScope)

  const tableFilters = useMemo(
    () => ({
      ...scope,
      category_ids: filters.categoryIds.length ? filters.categoryIds : undefined,
      q: filters.search || undefined,
      recurring_only: filters.recurringOnly || undefined,
      sort,
      order,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    }),
    [scope, filters.categoryIds, filters.search, filters.recurringOnly, sort, order, page],
  )

  const { data, isLoading, isError, error } = useTransactions(tableFilters)
  const { data: facets } = useTransactionFacets(tableFilters)

  // The leaderboard is its own query rather than a slice of the table's
  // page: it always shows the month's 5 biggest leftover outflows,
  // independent of the table's sort, filters, and pagination. `amount`
  // ascending puts the most negative (largest outflow) first.
  const { data: topSpend } = useTransactions({
    ...scope,
    sort: 'amount',
    order: 'asc',
    limit: LEADERBOARD_SIZE,
    offset: 0,
  })

  const slices = useUnbudgetedSlices(distribution?.entries ?? [])
  const unbudgetedTotal = Number(distribution?.total ?? 0)
  const hasPieData = slices.length > 0 && unbudgetedTotal > 0

  const leaders = useMemo(
    () => (topSpend?.items ?? []).filter((t) => Number(t.amount) < 0),
    [topSpend],
  )

  const handleFilterChange = (next: BudgetAnalysisFilterState) => {
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

  const handleRecategorized = (
    transactionId: number,
    description: string,
    info: RecategorizedInfo,
  ) => {
    if (info.categoryName === 'Uncategorized') return
    setPendingKeyword({
      transactionId,
      description,
      categoryId: info.categoryId,
      categoryName: info.categoryName,
    })
  }

  // Nothing is budgeted yet — the section would just restate the
  // Distribution page, so it stays out of the way until there's a
  // budget to be "outside of".
  if (expenses.length === 0) return null

  return (
    <section className={styles.section} data-testid="budget-analysis">
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>Where the rest went</h2>
          <p className={styles.sectionSubtitle}>
            Everything you spent in {monthLabel} that no budget expense accounted for — the
            categories you didn't plan for, your biggest unplanned hits, and every leftover
            record. Income and transfers sit outside this breakdown.
          </p>
        </div>
        <div className={styles.headlineTile}>
          <span className={styles.headlineLabel}>Unbudgeted spend</span>
          <span className={styles.headlineValue} data-testid="unbudgeted-total">
            {formatCurrency(unbudgetedTotal)}
          </span>
          <span className={styles.headlineSub}>
            across {slices.length} {slices.length === 1 ? 'category' : 'categories'}
          </span>
        </div>
      </div>

      <div className={styles.mosaic}>
        <div className={`${styles.tile} ${styles.pieTile}`}>
          <h3 className={styles.tileTitle}>Unbudgeted categories</h3>
          {pieLoading ? (
            <p className={styles.empty}>Loading…</p>
          ) : hasPieData ? (
            <div className={styles.pieLayout}>
              <DonutChart
                slices={slices}
                total={unbudgetedTotal}
                centerLabel="Unbudgeted"
                height={260}
                activeKey={activeKey}
                onHoverSlice={setActiveKey}
              />
              <div className={styles.legend}>
                {slices.map((slice) => (
                  <div
                    key={slice.key}
                    className={[
                      styles.legendRow,
                      activeKey && activeKey !== slice.key ? styles.legendRowMuted : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    onMouseEnter={() => setActiveKey(slice.key)}
                    onMouseLeave={() => setActiveKey(null)}
                    data-testid="unbudgeted-legend-row"
                    data-label={slice.label}
                  >
                    <span className={styles.swatch} style={{ background: slice.color }} />
                    <span className={styles.legendName}>{slice.label}</span>
                    <span className={styles.legendPercent}>
                      {formatPercent(slice.value / unbudgetedTotal)}
                    </span>
                    <span className={styles.legendAmount}>{formatCurrency(slice.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className={styles.empty}>
              Every dollar you spent in {monthLabel} landed in a budgeted category. Nice.
            </p>
          )}
        </div>

        <div className={`${styles.tile} ${styles.leaderTile}`}>
          <h3 className={styles.tileTitle}>Biggest unplanned hits</h3>
          {leaders.length > 0 ? (
            <ol className={styles.leaderboard}>
              {leaders.map((txn, index) => (
                <li
                  key={txn.id}
                  className={styles.leaderRow}
                  data-testid="unbudgeted-leader-row"
                >
                  <span className={styles.leaderRank}>{index + 1}</span>
                  <span className={styles.leaderBody}>
                    <span className={styles.leaderDescription} title={txn.description}>
                      {txn.description}
                    </span>
                    <span className={styles.leaderMeta}>
                      {txn.category_name ?? 'Uncategorized'} · {txn.txn_date}
                    </span>
                  </span>
                  <span className={styles.leaderAmount}>
                    {formatCurrencyPrecise(Math.abs(Number(txn.amount)))}
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className={styles.empty}>No unbudgeted spend this month.</p>
          )}
        </div>
      </div>

      <div className={`${styles.tile} ${styles.recordsTile}`}>
        <div className={styles.recordsHeader}>
          <h3 className={styles.tileTitle}>Leftover records</h3>
          <span className={styles.recordsCount}>
            {total} {total === 1 ? 'record' : 'records'}
          </span>
        </div>

        <FilterBar
          filters={{ ...filters, monthKeys: [], dateRange: undefined }}
          onChange={(next) =>
            handleFilterChange({
              accountIds: next.accountIds,
              categoryIds: next.categoryIds,
              search: next.search,
              includeExcluded: next.includeExcluded,
              recurringOnly: next.recurringOnly,
            })
          }
          totalCount={total}
          isLoading={isLoading}
          facets={facets}
          categoryOptions={unbudgetedCategories}
          hideMonths
          hideSearch
        />

        {isError && (
          <p className={styles.errorBanner}>
            {error instanceof ApiError ? error.message : 'Could not load leftover records.'}
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
          onPageChange={setPage}
          total={total}
          pageSize={PAGE_SIZE}
          onRecategorized={handleRecategorized}
          onRequestNewCategory={(transactionId, description) =>
            setPendingNewCategory({ transactionId, description })
          }
        />
      </div>

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
    </section>
  )
}
