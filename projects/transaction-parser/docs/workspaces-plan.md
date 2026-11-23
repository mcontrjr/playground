# Workspace management

Status: **complete and verified.** Branch `parser-2.0`.

## Decisions

| Question | Decision |
|---|---|
| How the workspace reaches the backend | `X-Workspace` header, resolved by one `get_workspace` dependency. No route paths changed. |
| Institutions | **global** (shared lookup, 6 rows, no `workspace_id`) — they are parser definitions, not user config. |
| Browser session | active workspace lives in a React context variable (`workspace`), mirrored to `sessionStorage` so F5 doesn't bounce to splash. |
| New-workspace defaults | generic buckets + categories, brand-neutral keywords. No budget. |
| Existing data | adopted into a workspace with slug **`init`** — no personal handle anywhere in schema or app. |

## Schema

`workspaces` (id, slug UNIQUE, name, timestamps). `workspace_id` FK
(ON DELETE CASCADE, NOT NULL) added to: accounts, ingest_batches,
parse_failures, transactions, buckets, categories, category_keywords,
budget_expenses, clash_dismissals, user_preferences, audit_events,
seed_suppressions.

Not added to `institutions` (global) or `budget_expense_categories`
(join table, scoped through both sides).

### Uniqueness re-scoped

| Constraint | Was | Now |
|---|---|---|
| `buckets.name` | global UNIQUE | `(workspace_id, name)` |
| `categories.name` | global UNIQUE | `(workspace_id, name)` |
| `category_keywords.keyword` | global UNIQUE | `(workspace_id, keyword)` |
| `uq_accounts_institution_hint` | (institution, hint) | + workspace_id |
| `uq_transactions_hash_occurrence` | (hash, occurrence) | + workspace_id |
| `uq_seed_suppressions_kind_name` | (kind, name) | + workspace_id |
| `user_preferences` PK | (key) | (workspace_id, key) |
| clash dismissal partial indexes | (winner, loser[, txn]) | + workspace_id |

**The transactions one is the load-bearing change.** `content_hash` is
derived from the statement's contents alone, so the same CSV hashes
identically in every workspace. Without the workspace in that
constraint, the second workspace's rows silently dedupe away as
already-ingested. Covered by `test_two_workspaces_can_ingest_the_same_csv`.

## Migration — `g1h2i3j4k5l6_workspaces.py`

Per table: add column nullable → backfill to `init` → SET NOT NULL → FK →
swap constraints. Verified against a **clone of the real database**
(486 transactions): upgrade adopts every row with zero nulls, downgrade
restores the old schema with data intact, and `alembic autogenerate`
reports no drift from the models.

**Applied to the dev database.** Backup at
`backups/pre-workspaces-20261122-220242.sql` (304K).

## Backend

- `app/models/workspace.py`, `app/deps.py` (`get_workspace`), `app/api/workspaces.py`,
  `app/schemas/workspaces.py`, `app/provisioning.py`.
- Endpoints (the only ones not needing the header):
  `GET /workspaces/{slug}`, `/{slug}/availability`, `POST /workspaces`,
  `GET /{slug}/bootstrap` (one call: accounts, buckets, categories,
  keywords, budget, `has_transactions`).
- Every query in `app/api/*` and `app/services/*` scoped. Structural
  choke points rather than per-query discipline:
  - `transactions._apply_filters` applies the workspace filter itself.
  - `AnalyticsFilters.workspace_id` is required and first — it flows into
    `_apply_filters` **and** into the `@cached` key. That cache is keyed on
    filters alone (the Session is excluded), so without it one workspace
    would be served another's cached totals.
  - `Categorizer.load(db, workspace_id=...)` and
    `category_service._load_snapshot` — unscoped these would categorize
    with another workspace's keywords.
  - `record_event(workspace_id=...)` is required, so a missed call site
    is a `TypeError` rather than a misfiled audit row.
- Writes taking client-supplied ids (`bulk-recategorize`,
  `clashes/resolve`) filter on workspace as well as id.
- `app/seed.py` keeps the personal category list, scoped to `init` only.
  New workspaces go through `provision_workspace` (generic defaults).

## Frontend

- `api/client.ts` — `setActiveWorkspaceSlug` injects `X-Workspace` at the
  one fetch choke point, so all ~25 existing query hooks were untouched.
- `workspace/WorkspaceContext.tsx` — `workspace` is the source of truth;
  entering/leaving clears the React Query cache.
- `pages/SplashPage.tsx` — spinning logo, enter-or-create, debounced
  availability check.
- `components/LogoSpinner/` — the one loading indicator (splash + first import).
- `App.tsx` / `Layout.tsx` — data pages hidden from the sidebar and
  guarded as routes until `has_transactions`. Categories stays available
  (configuration, not a report).
- `UploadPage` — first import shows the spinner, then unlocks the nav.

## Verification

- **208 backend tests pass** (178 pre-existing + 30 new).
- `tests/api/test_workspaces.py` covers the header guard, slug rules,
  provisioning, and isolation: transactions, categories, keywords,
  buckets, analytics (cache), preferences, audit, seed tombstones, plus
  attack paths (cross-workspace patch / bulk-recategorize are 404 / no-op).
- Frontend typechecks and builds.
- Exercised live in the browser: splash → enter `init` (486 txns, $25,935,
  8 accounts intact) → create a second workspace (gated sidebar, no leaked
  data) → import the same CSV `init` already had (105 inserted, 0 duplicates)
  → sidebar unlocks. Demo workspace then deleted.

## Follow-ups (not done)

- Playwright e2e specs still assume no splash screen; they need a setup
  step that enters a workspace.
- There is no auth: knowing a slug is enough to enter a workspace. Fine
  for local use, needs revisiting before a real deployment.
- No UI to rename or delete a workspace.
