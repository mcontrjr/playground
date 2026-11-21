import { useMemo, useState } from 'react'
import { ApiError } from '../api/client'
import { useBudgetSummary } from '../api/hooks/useBudget'
import {
  useCreateBudgetExpense,
  useDeleteBudgetExpense,
  usePatchBudgetExpense,
} from '../api/hooks/useBudgetMutations'
import { useCategories } from '../api/hooks/useCategories'
import { usePreference } from '../api/hooks/usePreference'
import { formatCurrency, formatCurrencyPrecise, formatMonthPeriod } from '../components/charts/format'
import { BudgetAnalysis } from '../components/BudgetAnalysis/BudgetAnalysis'
import { MonthSwiper } from '../components/MonthSwiper/MonthSwiper'
import { Modal } from '../components/Modal/Modal'
import { RecordsPanel } from '../components/RecordsPanel/RecordsPanel'
import { PlusIcon } from '../components/icons'
import type { BudgetExpense, Category, MonthlyBudgetTotal } from '../api/types'
import styles from './BudgetPage.module.css'

function toMonthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function monthKeyAdd(monthKey: string, delta: number): string {
  const [year, month] = monthKey.split('-').map(Number)
  const date = new Date(year!, month! - 1 + delta, 1)
  return toMonthKey(date)
}

function monthKeyBounds(monthKey: string): { date_from: string; date_to: string } {
  const [year, month] = monthKey.split('-').map(Number)
  const lastDay = new Date(year!, month!, 0).getDate()
  return { date_from: `${monthKey}-01`, date_to: `${monthKey}-${String(lastDay).padStart(2, '0')}` }
}

/** The current real-world month — Budget always allows navigating up
 * to "now" (there's no data-driven ceiling like Overview/Time Series'
 * useMonthScope, since a budget can exist for a month with zero
 * transactions so far). */
const CURRENT_MONTH_KEY = toMonthKey(new Date())

function progressRatio(actual: number, goal: number | null): number {
  if (goal == null || goal <= 0) return 0
  return Math.min(1, actual / goal)
}

function CategoryLinkPicker({
  categories,
  selected,
  onToggle,
  takenByName,
}: {
  categories: Category[]
  selected: number[]
  onToggle: (categoryId: number) => void
  /** category id -> name of the other expense that already claims it
   * this month. A taken category can't be toggled on here — a
   * category funds at most one expense's actual-amount total, so
   * double-linking it would double-count the same transactions. */
  takenByName: Map<number, string>
}) {
  const sorted = [...categories].sort((a, b) => a.name.localeCompare(b.name))
  return (
    <div className={styles.categoryPicker} role="group" aria-label="Link categories">
      {sorted.map((category) => {
        const isActive = selected.includes(category.id)
        const takenBy = takenByName.get(category.id)
        return (
          <button
            key={category.id}
            type="button"
            className={isActive ? `${styles.categoryChip} ${styles.categoryChipActive}` : styles.categoryChip}
            onClick={() => onToggle(category.id)}
            aria-pressed={isActive}
            disabled={!!takenBy}
            title={takenBy ? `Already linked to "${takenBy}"` : undefined}
          >
            {category.name}
          </button>
        )
      })}
    </div>
  )
}

interface ExpenseDialogProps {
  month: string
  expense: BudgetExpense | null
  /** Every other expense already on this month's budget — used to
   * take their linked categories out of the pool so the same category
   * can't fund two expenses' totals at once. */
  otherExpenses: BudgetExpense[]
  onClose: () => void
}

function ExpenseDialog({ month, expense, otherExpenses, onClose }: ExpenseDialogProps) {
  const { data: categories } = useCategories()
  const [name, setName] = useState(expense?.name ?? '')
  const [goalAmount, setGoalAmount] = useState(expense?.goal_amount ?? '')
  const [isFixed, setIsFixed] = useState(expense?.is_fixed ?? false)
  const [categoryIds, setCategoryIds] = useState<number[]>(expense?.categories.map((c) => c.id) ?? [])

  const takenByName = useMemo(() => {
    const map = new Map<number, string>()
    for (const other of otherExpenses) {
      for (const category of other.categories) map.set(category.id, other.name)
    }
    return map
  }, [otherExpenses])

  const createExpense = useCreateBudgetExpense(month)
  const patchExpense = usePatchBudgetExpense(month)
  const mutation = expense ? patchExpense : createExpense
  const isEdit = !!expense

  const toggleCategory = (categoryId: number) => {
    setCategoryIds((current) =>
      current.includes(categoryId) ? current.filter((id) => id !== categoryId) : [...current, categoryId],
    )
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmedName = name.trim()
    if (!trimmedName) return
    const goal = !isFixed && goalAmount.trim() ? goalAmount.trim() : null

    if (isEdit) {
      patchExpense.mutate(
        { id: expense.id, patch: { name: trimmedName, goal_amount: goal, is_fixed: isFixed, category_ids: categoryIds } },
        { onSuccess: onClose },
      )
    } else {
      createExpense.mutate(
        { name: trimmedName, goal_amount: goal, is_fixed: isFixed, category_ids: categoryIds },
        { onSuccess: onClose },
      )
    }
  }

  return (
    <Modal title={isEdit ? 'Edit expense' : 'New expense'} onClose={onClose} ariaLabel="Budget expense">
      <form onSubmit={submit}>
        <div className={styles.formField}>
          <label className={styles.formLabel} htmlFor="expense-name">
            Name
          </label>
          <input
            id="expense-name"
            className={styles.formInput}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            placeholder="e.g. Groceries"
            data-testid="expense-name-input"
          />
        </div>

        <div className={styles.formField}>
          <label className={styles.fixedToggle} htmlFor="expense-is-fixed">
            <input
              id="expense-is-fixed"
              type="checkbox"
              checked={isFixed}
              onChange={(e) => setIsFixed(e.target.checked)}
              data-testid="expense-is-fixed-checkbox"
            />
            Fixed monthly expense
          </label>
          <p className={styles.formHint}>
            A known recurring amount (e.g. Rent) rather than a goal to hit — fixed expenses don't track against a goal.
          </p>
        </div>

        {!isFixed && (
          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="expense-goal">
              Monthly goal (optional)
            </label>
            <input
              id="expense-goal"
              className={styles.formInput}
              value={goalAmount}
              onChange={(e) => setGoalAmount(e.target.value)}
              placeholder="e.g. 600.00"
              inputMode="decimal"
              data-testid="expense-goal-input"
            />
          </div>
        )}

        <div className={styles.formField}>
          <span className={styles.formLabel}>Link categories</span>
          <p className={styles.formHint}>
            Transactions in linked categories are summed automatically into this expense's actual amount — no manual entry needed.
          </p>
          <CategoryLinkPicker
            categories={categories ?? []}
            selected={categoryIds}
            onToggle={toggleCategory}
            takenByName={takenByName}
          />
        </div>

        {mutation.isError && (
          <p className={styles.errorBanner}>
            {mutation.error instanceof ApiError ? mutation.error.message : 'Could not save expense.'}
          </p>
        )}

        <div className={styles.confirmActions}>
          <button type="button" className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={styles.addButton}
            disabled={!name.trim() || mutation.isPending}
            data-testid="submit-expense"
          >
            {mutation.isPending ? 'Saving…' : isEdit ? 'Save changes' : 'Create expense'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function ExpenseRow({
  expense,
  month,
  onEdit,
  onToggleRecords,
  isExpanded,
}: {
  expense: BudgetExpense
  month: string
  onEdit: () => void
  onToggleRecords: () => void
  isExpanded: boolean
}) {
  const deleteExpense = useDeleteBudgetExpense()
  const actual = Number(expense.actual_amount)
  const goal = expense.goal_amount != null ? Number(expense.goal_amount) : null
  const ratio = progressRatio(actual, goal)
  const overBudget = goal != null && actual > goal

  return (
    <div className={styles.expenseRow} data-testid="budget-expense-row">
      <div className={styles.expenseHeader}>
        <button type="button" className={styles.expenseName} onClick={onToggleRecords} data-testid="expense-name-button">
          {expense.name}
        </button>
        <div className={styles.expenseActions}>
          <button type="button" className={styles.linkButton} onClick={onEdit} data-testid="edit-expense-button">
            Edit
          </button>
          <button
            type="button"
            className={styles.linkButtonDanger}
            onClick={() => deleteExpense.mutate(expense.id)}
            data-testid="delete-expense-button"
          >
            Delete
          </button>
        </div>
      </div>

      <div className={styles.categoryTags}>
        {expense.categories.length > 0 ? (
          expense.categories.map((c) => (
            <span className={styles.categoryTag} key={c.id}>
              {c.name}
            </span>
          ))
        ) : (
          <span className={styles.noCategoriesHint}>No categories linked — add some to auto-total this expense.</span>
        )}
      </div>

      {!expense.is_fixed && (
        <div className={styles.progressTrack}>
          <div
            className={overBudget ? `${styles.progressFill} ${styles.progressFillOver}` : styles.progressFill}
            style={{ width: `${ratio * 100}%` }}
          />
        </div>
      )}

      <div className={styles.amountsRow}>
        <span className={overBudget ? styles.amountOver : styles.amount}>{formatCurrencyPrecise(actual)}</span>
        <span className={styles.amountGoal}>
          {expense.is_fixed ? 'Fixed expense' : goal != null ? `of ${formatCurrencyPrecise(goal)} goal` : 'no goal set'}
        </span>
      </div>

      {isExpanded && (
        <RecordsPanel
          title={expense.name}
          filters={{
            ...monthKeyBounds(month),
            category_ids: expense.categories.map((c) => c.id),
          }}
          onClose={onToggleRecords}
        />
      )}
    </div>
  )
}

/** The monthly budget total: a single, un-month-scoped preference
 * value that carries forward across months until the user changes it
 * (pay periods vary per income source, so this is user-set rather
 * than auto-imported from an Income category the way it used to be).
 * `remaining` reserves both fixed expenses (their actual amount, since
 * they don't track against a goal) and non-fixed expenses' goal
 * amounts (the planned target, not actual spend so far) — so setting
 * a goal immediately carves out its share of the budget regardless of
 * how much of it has actually been spent yet. */
function MonthlyBudgetTile({ totalFixed, totalGoal }: { totalFixed: number; totalGoal: number }) {
  const [budgetTotal, setBudgetTotal, { isReady }] = usePreference<MonthlyBudgetTotal>('budget:monthly_total', {
    amount: '',
  })
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(budgetTotal.amount)

  const budgetAmount = Number(budgetTotal.amount || 0)
  const remaining = budgetAmount - totalFixed - totalGoal

  const commit = () => {
    setBudgetTotal({ amount: draft.trim() })
    setEditing(false)
  }

  return (
    <>
      <div className={styles.summaryTile}>
        <span className={styles.summaryLabel}>Monthly budget</span>
        {editing ? (
          <input
            className={styles.summaryInput}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commit()
              if (e.key === 'Escape') {
                setDraft(budgetTotal.amount)
                setEditing(false)
              }
            }}
            inputMode="decimal"
            placeholder="e.g. 4500.00"
            autoFocus
            data-testid="monthly-budget-input"
          />
        ) : (
          <button
            type="button"
            className={styles.summaryValueButton}
            onClick={() => {
              setDraft(budgetTotal.amount)
              setEditing(true)
            }}
            disabled={!isReady}
            data-testid="monthly-budget-value"
          >
            {budgetAmount > 0 ? formatCurrency(budgetAmount) : 'Set budget'}
          </button>
        )}
      </div>
      <div className={styles.summaryTile}>
        <span className={styles.summaryLabel}>Total fixed expenses</span>
        <span className={styles.summaryValue}>{formatCurrency(totalFixed)}</span>
      </div>
      <div className={styles.summaryTile}>
        <span className={styles.summaryLabel}>Goal-tracked expenses</span>
        <span className={styles.summaryValue}>{formatCurrency(totalGoal)}</span>
      </div>
      <div className={styles.summaryTile}>
        <span className={styles.summaryLabel}>Remaining</span>
        <span className={remaining < 0 ? styles.summaryValueNegative : styles.summaryValuePositive}>
          {formatCurrency(remaining)}
        </span>
      </div>
    </>
  )
}

/** Fixed expenses sink to the bottom; the remaining goal-tracked
 * expenses are ordered by goal amount, largest first, with
 * goal-less ones last (within that group). */
function sortExpenses(expenses: BudgetExpense[]): BudgetExpense[] {
  return [...expenses].sort((a, b) => {
    if (a.is_fixed !== b.is_fixed) return a.is_fixed ? 1 : -1
    if (a.is_fixed) return 0
    const goalA = a.goal_amount != null ? Number(a.goal_amount) : -Infinity
    const goalB = b.goal_amount != null ? Number(b.goal_amount) : -Infinity
    return goalB - goalA
  })
}

export function BudgetPage() {
  const [monthKey, setMonthKey] = useState(CURRENT_MONTH_KEY)
  const [showAdd, setShowAdd] = useState(false)
  const [editingExpense, setEditingExpense] = useState<BudgetExpense | null>(null)
  const [expandedExpenseId, setExpandedExpenseId] = useState<number | null>(null)

  const { data: summary, isLoading, isError, error } = useBudgetSummary(monthKey)

  const sortedExpenses = useMemo(() => (summary ? sortExpenses(summary.expenses) : []), [summary])

  const totalActual = Number(summary?.total_actual ?? 0)
  const totalGoal = Number(summary?.total_goal ?? 0)
  const totalFixed = Number(summary?.total_fixed ?? 0)

  const monthLabel = useMemo(() => formatMonthPeriod(monthKey), [monthKey])
  const monthBounds = useMemo(() => monthKeyBounds(monthKey), [monthKey])
  const isCurrentMonth = monthKey === CURRENT_MONTH_KEY

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Budget</h1>
        <p className={styles.subtitle}>
          Set your total monthly budget, mark fixed recurring expenses, and track the rest against
          their goals.
        </p>
      </header>

      <MonthSwiper
        label={monthLabel}
        canGoNewer={!isCurrentMonth}
        canGoOlder
        badge={isCurrentMonth ? 'Current month' : undefined}
        onNewer={() => setMonthKey((k) => monthKeyAdd(k, 1))}
        onOlder={() => setMonthKey((k) => monthKeyAdd(k, -1))}
      />

      {isError && (
        <p className={styles.errorBanner}>
          {error instanceof ApiError ? error.message : 'Could not load the budget.'}
        </p>
      )}

      {isLoading ? (
        <p className={styles.empty}>Loading…</p>
      ) : (
        <>
          <div className={styles.summaryTiles}>
            <MonthlyBudgetTile totalFixed={totalFixed} totalGoal={totalGoal} />
          </div>
          {totalGoal > 0 && (
            <p className={styles.summaryHint}>
              Non-fixed expense goals this month total {formatCurrency(totalGoal)}; actual spend against
              them so far is {formatCurrency(totalActual - totalFixed)}.
            </p>
          )}

          <div className={styles.listHeader}>
            <h2 className={styles.listHeading}>Expenses</h2>
            <button
              type="button"
              className={styles.addButton}
              onClick={() => setShowAdd(true)}
              data-testid="open-add-expense"
            >
              <PlusIcon /> Add expense
            </button>
          </div>

          {summary && sortedExpenses.length > 0 ? (
            <div className={styles.expenseList}>
              {sortedExpenses.map((expense) => (
                <ExpenseRow
                  key={expense.id}
                  expense={expense}
                  month={monthKey}
                  onEdit={() => setEditingExpense(expense)}
                  isExpanded={expandedExpenseId === expense.id}
                  onToggleRecords={() =>
                    setExpandedExpenseId((current) => (current === expense.id ? null : expense.id))
                  }
                />
              ))}
            </div>
          ) : (
            <p className={styles.empty}>No budget expenses yet — add one to start tracking.</p>
          )}

          {/* The breakdown of everything this month that no expense
              above accounted for. Renders nothing until there's at
              least one expense to be "outside of". */}
          <BudgetAnalysis
            monthLabel={monthLabel}
            expenses={summary?.expenses ?? []}
            dateFrom={monthBounds.date_from}
            dateTo={monthBounds.date_to}
          />
        </>
      )}

      {showAdd && (
        <ExpenseDialog
          month={monthKey}
          expense={null}
          otherExpenses={summary?.expenses ?? []}
          onClose={() => setShowAdd(false)}
        />
      )}
      {editingExpense && (
        <ExpenseDialog
          month={monthKey}
          expense={editingExpense}
          otherExpenses={(summary?.expenses ?? []).filter((e) => e.id !== editingExpense.id)}
          onClose={() => setEditingExpense(null)}
        />
      )}
    </div>
  )
}
