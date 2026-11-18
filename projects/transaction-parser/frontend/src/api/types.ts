/**
 * Hand-written TypeScript interfaces mirroring the backend's Pydantic
 * schemas (see /openapi.json served by the FastAPI app). Keep these in
 * sync manually — there is no codegen step in this project.
 */

// ---------------------------------------------------------------------------
// Accounts
// ---------------------------------------------------------------------------

export interface Account {
  id: number
  institution_code: string
  institution_name: string
  account_hint: string
  display_name: string
  kind: 'card' | 'checking'
  transaction_count: number
}

export interface AccountPatch {
  display_name: string
}

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------

export interface CategoryKeyword {
  id: number
  keyword: string
}

export interface Category {
  id: number
  name: string
  is_system: boolean
  excluded_from_analytics: boolean
  priority: number
  /** Uppercase bucket name, serialized from the related `Bucket` —
   * kept for display/back-compat even though assignment now goes
   * through `bucket_id`. */
  group: string | null
  bucket_id: number
  keywords: CategoryKeyword[]
  transaction_count: number
}

export interface CategoryCreate {
  name: string
  excluded_from_analytics?: boolean
  priority?: number
  bucket_id?: number
}

export interface CategoryPatch {
  name?: string
  excluded_from_analytics?: boolean
  priority?: number
  bucket_id?: number
}

export interface CategoryPatchResponse {
  category: Category
  affected_transaction_count: number
}

export interface CategoryDeleteResponse {
  deleted_category_id: number
  reassigned_transaction_count: number
}

export interface CategoryKeywordCreate {
  keyword: string
  apply_to_existing: boolean
}

export interface CategoryKeywordCreateResponse {
  keyword: CategoryKeyword
  applied_count: number
}

export interface CategoryKeywordDeleteResponse {
  deleted_keyword_id: number
  reapplied_count: number
}

export type ImpactPreviewAction = 'add_keyword' | 'remove_keyword'

export interface ImpactPreviewRequest {
  category_id: number
  keyword: string
  action: ImpactPreviewAction
}

export interface ImpactPreviewTransaction {
  id: number
  description: string
  current_category_id: number | null
  current_category_name: string | null
  new_category_id: number | null
  new_category_name: string | null
}

export interface ImpactPreviewBreakdownEntry {
  from_category_id: number | null
  from_category: string
  to_category_id: number | null
  to_category: string
  count: number
}

export interface ImpactPreviewResponse {
  affected_count: number
  sample: ImpactPreviewTransaction[]
  breakdown: ImpactPreviewBreakdownEntry[]
}

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------

export type CategorySource = 'keyword' | 'manual' | 'transfer' | 'default'
export type Recurrence = 'monthly' | 'yearly'

export interface Transaction {
  id: number
  account_id: number
  account_name: string
  /** The source bank/card, e.g. 'schwab', 'amex' — keys which raw_row
   * columns to expect; never assume another institution's shape. */
  institution_code: string
  batch_id: number
  txn_date: string // ISO date
  posted_date: string | null
  description: string
  /** Signed decimal string; negative = money out, positive = money in. */
  amount: string
  bank_category: string | null
  category_id: number | null
  category_name: string | null
  category_source: CategorySource
  is_recurring: boolean
  recurrence: Recurrence | null
  /** The original CSV row, keyed by that bank's own column names. Shape
   * differs per institution_code — never padded with nulls for columns
   * a different bank happens to have. */
  raw_row: Record<string, string>
  created_at: string
}

export interface TransactionListResponse {
  items: Transaction[]
  total: number
  limit: number
  offset: number
}

export interface TransactionPatch {
  category_id?: number
  is_recurring?: boolean
  recurrence?: Recurrence | null
}

export type TransactionSortField = 'txn_date' | 'amount' | 'description' | 'category'
export type SortOrder = 'asc' | 'desc'

export interface TransactionFilters {
  date_from?: string
  date_to?: string
  account_ids?: number[]
  category_ids?: number[]
  q?: string
  recurring_only?: boolean
  include_excluded?: boolean
  sort?: TransactionSortField
  order?: SortOrder
  limit?: number
  offset?: number
}

export interface MonthOption {
  /** "YYYY-MM" */
  key: string
  label: string
  from: string
  to: string
}

// ---------------------------------------------------------------------------
// Uploads / ingest batches
// ---------------------------------------------------------------------------

export interface BatchCounts {
  total: number
  inserted: number
  duplicates: number
  failures: number
}

export interface ParseFailure {
  id: number
  batch_id: number
  line_number: number
  raw_line: string
  error_type: string
  error_message: string
  resolved: boolean
  created_at: string
}

export interface BatchSummary {
  id: number
  filename: string
  institution: string
  status: 'completed' | 'completed_with_errors' | 'failed'
  counts: BatchCounts
  created_at: string
}

export interface BatchDetail extends BatchSummary {
  failures: ParseFailure[]
}

export interface ParseFailurePatch {
  resolved: boolean
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface AnalyticsSummary {
  total_spent: string
  total_in: string
  net: string
  transaction_count: number
  date_from: string | null
  date_to: string | null
  avg_monthly_spend: string
  largest_transaction: string | null
}

export type Granularity = 'month' | 'day'

export interface TimeseriesSeriesPoint {
  period: string
  value: string
}

export interface TimeseriesSeries {
  category_id: number | null
  name: string
  values: TimeseriesSeriesPoint[]
}

export interface TimeseriesResponse {
  granularity: Granularity
  periods: string[]
  series: TimeseriesSeries[]
}

export interface DailyCategoryAmount {
  category_id: number | null
  name: string
  amount: string
}

export interface DailyPoint {
  date: string // ISO date
  value: string
  running_total: string
  by_category: DailyCategoryAmount[]
}

export interface MonthlyDailySeries {
  month: string // "YYYY-MM"
  label: string
  points: DailyPoint[]
  month_total: string
}

export interface DistributionEntry {
  category_id: number
  name: string
  amount: string
}

export interface DistributionResponse {
  entries: DistributionEntry[]
  total: string
}

export interface AnalyticsFilters {
  date_from?: string
  date_to?: string
  account_ids?: number[]
  include_excluded?: boolean
}

// ---------------------------------------------------------------------------
// Buckets
// ---------------------------------------------------------------------------

export interface Bucket {
  id: number
  name: string
  category_count: number
}

export interface BucketCreate {
  name: string
}

export interface BucketUpdate {
  name: string
}

export interface BucketDeleteResult {
  moved_category_count: number
  reassigned_to_bucket_id: number
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export type AuditEventType =
  | 'category.created'
  | 'category.renamed'
  | 'category.deleted'
  | 'category.bucket_changed'
  | 'keyword.added'
  | 'keyword.removed'
  | 'transaction.recategorized'
  | 'bucket.created'
  | 'bucket.renamed'
  | 'bucket.deleted'

export interface AuditEvent {
  id: number
  event_type: AuditEventType
  entity_type: string
  entity_id: number | null
  description: string
  payload: Record<string, unknown> | null
  affected_count: number | null
  created_at: string
}

export interface AuditPage {
  items: AuditEvent[]
  total: number
  limit: number
  offset: number
}

// ---------------------------------------------------------------------------
// Budget
// ---------------------------------------------------------------------------

export interface BudgetCategoryRef {
  id: number
  name: string
}

export interface BudgetExpense {
  id: number
  name: string
  goal_amount: string | null
  sort_order: number
  categories: BudgetCategoryRef[]
  actual_amount: string
}

export interface BudgetExpenseCreate {
  name: string
  goal_amount?: string | null
  category_ids: number[]
}

export interface BudgetExpenseUpdate {
  name?: string
  goal_amount?: string | null
  category_ids?: number[]
  sort_order?: number
}

export interface BudgetExpenseDeleteResult {
  deleted_budget_expense_id: number
}

export interface BudgetSummary {
  /** "YYYY-MM" */
  month: string
  income: string
  total_goal: string
  total_actual: string
  expenses: BudgetExpense[]
}

// ---------------------------------------------------------------------------
// Preferences (server-side cache of theme + per-page filter state)
// ---------------------------------------------------------------------------

/** Preferences are opaque JSON objects — any plain object shape the
 * frontend defines is valid; the server never interprets the fields. */
export type PreferenceValue = Record<string, unknown>

export interface Preference {
  key: string
  value: PreferenceValue
}

// ---------------------------------------------------------------------------
// Error shapes
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  code: string
  message: string
  owning_category_id?: number | null
  owning_category_name?: string | null
}

export interface AmbiguousInstitutionDetail {
  code: 'AMBIGUOUS_INSTITUTION'
  candidates: string[]
  message: string
}

export interface ValidationErrorItem {
  loc: (string | number)[]
  msg: string
  type: string
}

export interface HTTPValidationError {
  detail: ValidationErrorItem[]
}
