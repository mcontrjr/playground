# frontend

React dashboard for the transaction-parser backend — upload bank CSVs, browse the
categorized ledger, and inspect spend over time.

- **Stack:** Vite, React 19, TypeScript, React Router (routes = tabs), TanStack
  Query (server state + cache invalidation), Recharts (SVG charts styled via CSS
  vars). No component library — hand-rolled CSS Modules on top of `tokens.css`.
- **Dev server:** `npm run dev` (port 5173 in-container, proxied to host `5174` by
  docker-compose). Vite's dev server proxies `/api/*` to the backend container by
  service name, so there's no CORS configuration anywhere in this app.

## Component map

```
src/
├── main.tsx                 React root, QueryClientProvider, router
├── App.tsx                  Routes (= top-level tabs)
├── theme/tokens.css          design tokens (see below)
├── api/
│   ├── client.ts             fetch wrapper, ApiError, buildQuery
│   ├── queryKeys.ts           centralized query-key factory
│   ├── types.ts               hand-written mirrors of the backend's Pydantic schemas
│   └── hooks/                 one file per resource: useTransactions, useCategories,
│                               useCategoryMutations, useUploadFile, useFailures,
│                               useBatches, useAccounts, usePatchTransaction, useAnalytics
├── components/
│   ├── Layout/                 shell: wordmark, tab nav, unresolved-failures badge
│   ├── FilterBar/               FilterBar (Records) + AnalyticsFilterBar (charts),
│   │                             FilterChipGroup, ScopeToggle (shared transfers toggle)
│   ├── TransactionsTable/       sortable/paginated table + inline CategoryPicker
│   ├── CategoryPicker/          inline <select> + "also add keyword" follow-up
│   ├── UploadDropzone/          drag/drop + file picker
│   ├── InstitutionPickerDialog/ the CapOne/Discover 409 disambiguation modal
│   ├── ImpactPreviewDialog/     dry-run preview before a keyword add/remove/rename
│   ├── BatchList/, FailuresList/  upload history / parse failures
│   ├── Modal/                    shared dialog shell (overlay, Esc-to-close)
│   └── charts/                   KpiTile, DonutChart, StackedBarChart, MiniBarChart,
│                                   ChartLegend, ChartTooltip, palette.ts, format.ts
└── pages/                     OverviewPage, TimeSeriesPage, DistributionPage,
                                RecordsPage, CategoriesPage, UploadPage
```

Routes double as tabs (`/overview`, `/time-series`, `/distribution`, `/records`,
`/categories`, `/upload`); `/` redirects to `/records`.

## Data-layer conventions

- **One hook per endpoint**, under `api/hooks/`. Hooks call the typed `api.get` /
  `api.post` / `api.patch` / `api.delete` / `api.postForm` helpers from
  `api/client.ts`, which throw a structured `ApiError` (with `.status`, `.code`,
  `.detail`) on any non-2xx response so callers can branch on FastAPI's structured
  error codes (e.g. `AMBIGUOUS_INSTITUTION`) without re-parsing JSON.
- **Query keys** are centralized in `api/queryKeys.ts` rather than inlined per
  hook, so invalidation call sites and query call sites can't drift out of sync.
  Parameterized keys (`transactions(filters)`, `analyticsSummary(params)`) include
  the filter object so distinct filter combinations cache independently.
- **Invalidation on mutation**: every mutation hook (`useUploadFile`,
  `usePatchTransaction`, `useCategoryMutations`, `usePatchFailure`, ...)
  invalidates the relevant query keys in `onSuccess` — e.g. uploading a file
  invalidates batches, transactions, accounts, categories, failures, *and*
  analytics in one shot, since a new batch can touch all of them. This is what
  keeps the dashboard live without manual refetching.
- **No codegen**: `api/types.ts` is hand-maintained against the backend's Pydantic
  schemas (viewable at `/docs`). Keep the two in sync by hand when either side
  changes a field.

## Design tokens

`src/theme/tokens.css` defines the whole visual system as CSS custom properties —
a near-monochrome editorial look (ink `#3E3A49` on white, 1px hairline rules
instead of boxed cards, dark rounded KPI tiles as the one "solid" surface,
Montserrat throughout). Key groups:

- **Core palette**: `--ink`/`--ink-soft`/`--ink-faint` text tones, `--paper`/
  `--paper-sunk` backgrounds, `--hairline`/`--hairline-strong` rule colors.
- **Tile**: `--tile-bg`/`--tile-fg` for the dark KPI tiles.
- **Semantic accents**: `--accent-negative` (money out), `--accent-positive`
  (money in), `--accent-focus` — used sparingly, never as the primary UI color.
- **Categorical chart palette**: `--series-1` through `--series-8` plus
  `--series-other`, desaturated and fixed-order (never reassigned when the series
  count changes); a 9th+ category always folds into "Other" rather than minting a
  new hue. Validated for CVD-safe contrast — see `components/charts/palette.ts`
  for the assignment logic.
- **Type scale** and `--tracking-wide`/`--tracking-wider` for the uppercase,
  letter-spaced nav/label treatment.

Components consume tokens via CSS Modules (`*.module.css`) — no inline styles, no
CSS-in-JS.

## Chart kit

`components/charts/` is a small internal kit on top of Recharts, not a generic
wrapper library — each chart (`DonutChart`, `StackedBarChart`, `MiniBarChart`)
hard-codes the project's styling (axis/grid colors from tokens, `ChartTooltip` /
`ChartLegend` shared across charts) rather than exposing a themeable prop surface.
`palette.ts` owns categorical color assignment (`assignSeriesColors`, the "Other"
fold-in rule); `format.ts` owns currency/percent/period formatting shared between
KPI tiles, tooltips, and axis ticks.

## E2E tests

See `e2e/` (Playwright). Requires the full stack already running via
`docker compose up` — these tests drive the real app over HTTP, they don't start
their own server.

```bash
npm run e2e          # playwright test (system Chromium, see playwright.config.ts)
npm run e2e:report   # open the last HTML report (frontend/playwright-report/)
```
