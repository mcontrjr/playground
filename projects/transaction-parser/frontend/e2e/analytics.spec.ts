import { test, expect } from '@playwright/test'

/**
 * Overview KPI tiles against the live /analytics/summary payload,
 * Distribution's transfers-excluded-by-default behavior, and Time
 * Series' stacked bar chart + legend rendering.
 */

test('Overview KPI tiles render non-empty currency values matching the summary API', async ({ page, request }) => {
  const response = await request.get('http://localhost:58000/api/v1/analytics/summary')
  expect(response.ok()).toBeTruthy()
  const summary = await response.json()

  await page.goto('/overview')

  const totalSpentTile = page.getByTestId('kpi-tile').filter({ hasText: 'Total spent' })
  const totalSpentValueLocator = totalSpentTile.getByTestId('kpi-tile-value')
  // KPI tiles render whole-dollar amounts (maximumFractionDigits: 0),
  // so match "$35,291" rather than a cents-precision pattern. Wait for
  // the loading placeholder ("—") to resolve before reading content.
  await expect(totalSpentValueLocator).toHaveText(/\$[\d,]+/, { timeout: 10_000 })
  const totalSpentValue = await totalSpentValueLocator.textContent()

  const expectedSpent = Number(summary.total_spent)
  const renderedSpent = Number(totalSpentValue!.replace(/[^0-9.]/g, ''))
  expect(Math.abs(renderedSpent - expectedSpent)).toBeLessThan(1)

  const transactionsTile = page.getByTestId('kpi-tile').filter({ hasText: 'Transactions' })
  const transactionsValueLocator = transactionsTile.getByTestId('kpi-tile-value')
  await expect(transactionsValueLocator).not.toHaveText('—', { timeout: 10_000 })
  const transactionsValue = await transactionsValueLocator.textContent()
  expect(Number(transactionsValue!.replace(/[^0-9]/g, ''))).toBe(summary.transaction_count)
})

test('Distribution excludes Payments & Transfers by default, shows it when toggled on', async ({ page }) => {
  await page.goto('/distribution')
  await expect(page.getByTestId('distribution-row').first()).toBeVisible({ timeout: 10_000 })

  await expect(page.getByTestId('distribution-row').filter({ hasText: 'Payments & Transfers' })).toHaveCount(0)

  // The checkbox itself is visually hidden (opacity:0, 1x1) behind a
  // styled switch — force the check since Playwright's actionability
  // check would otherwise wait forever for it to become "visible".
  await page.getByTestId('scope-toggle-input').check({ force: true })
  await expect
    .poll(
      async () => page.getByTestId('distribution-row').filter({ hasText: 'Payments & Transfers' }).count(),
      { timeout: 10_000 },
    )
    .toBeGreaterThan(0)
})

test('Time Series renders stacked bars and a legend', async ({ page }) => {
  await page.goto('/time-series')

  const chart = page.locator('svg').first()
  await expect(chart).toBeVisible({ timeout: 10_000 })
  // Recharts renders each stacked-bar segment inside a
  // ".recharts-bar-rectangle" group; assert at least one is present
  // rather than matching any <rect> (the chart grid/axes also use
  // <rect> elements that aren't the bars themselves).
  await expect(chart.locator('.recharts-bar-rectangle').first()).toBeAttached({ timeout: 10_000 })
  const barCount = await chart.locator('.recharts-bar-rectangle').count()
  expect(barCount).toBeGreaterThan(0)

  const legend = page.getByRole('list').filter({ has: page.getByRole('listitem') }).first()
  await expect(legend).toBeVisible()
  const legendItems = legend.getByRole('listitem')
  await expect(legendItems.first()).toBeVisible()
  expect(await legendItems.count()).toBeGreaterThan(0)
})
