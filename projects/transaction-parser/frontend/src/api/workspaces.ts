/**
 * Workspace lifecycle calls. These are the only endpoints that take the
 * slug in the path rather than the `X-Workspace` header — the splash
 * screen talks to them before any workspace is active.
 */
import { api } from './client'
import type { Account, Bucket, Category } from './types'

export interface Workspace {
  id: number
  slug: string
  name: string
}

export interface SlugAvailability {
  slug: string
  available: boolean
  reason: string | null
}

export interface BudgetExpenseLite {
  id: number
  name: string
  goal_amount: string | null
  is_fixed: boolean
  sort_order: number
  categories: { id: number; name: string }[]
  actual_amount: string
}

export interface WorkspaceBootstrap {
  workspace: Workspace
  /** False until the first successful upload — gates the data pages. */
  has_transactions: boolean
  transaction_count: number
  accounts: Account[]
  buckets: Bucket[]
  categories: Category[]
  budget_expenses: BudgetExpenseLite[]
}

/** Slug rules, mirrored from the backend so the form can validate early. */
export const SLUG_PATTERN = /^[a-z0-9][a-z0-9_-]{1,39}$/
export const SLUG_RULES =
  '2–40 characters, starting with a letter or number. Lowercase letters, numbers, hyphens and underscores only.'

export function normalizeSlug(raw: string): string {
  return raw.trim().toLowerCase()
}

export const workspacesApi = {
  get: (slug: string) =>
    api.get<Workspace>(`/workspaces/${encodeURIComponent(normalizeSlug(slug))}`),

  availability: (slug: string) =>
    api.get<SlugAvailability>(
      `/workspaces/${encodeURIComponent(normalizeSlug(slug))}/availability`,
    ),

  create: (slug: string, name?: string) =>
    api.post<Workspace>('/workspaces', {
      slug: normalizeSlug(slug),
      ...(name && name.trim() ? { name: name.trim() } : {}),
    }),

  bootstrap: (slug: string) =>
    api.get<WorkspaceBootstrap>(
      `/workspaces/${encodeURIComponent(normalizeSlug(slug))}/bootstrap`,
    ),
}
