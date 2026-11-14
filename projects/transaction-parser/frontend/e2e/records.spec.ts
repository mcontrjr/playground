import { test, expect } from '@playwright/test'

/**
 * Exercises the Records page: default/transfers-toggle count, search
 * filtering, sort-by-amount, and inline recategorization. The last
 * part targets the two synthetic "E2E TEST ROW ONE/TWO" transactions
 * inserted by failures.spec.ts (must run first — Playwright's default
 * alphabetical file order already puts "failures" before "records").
 * The category is flipped to a non-system category and back to
 * Uncategorized so the net effect on the DB is a no-op.
 */

test.describe.configure({ mode: 'serial' })

test('default count is smaller than the transfers-included count', async ({ page }) => {
  await page.goto('/records')

  const countIndicator = page.getByTestId('records-result-count')
  await expect(countIndicator).toBeVisible()
  await expect(page.getByTestId('transaction-row').first()).toBeVisible({ timeout: 10_000 })

  const defaultCount = Number(await countIndicator.getAttribute('data-count'))
  expect(defaultCount).toBeGreaterThan(0)

  // The checkbox itself is visually hidden (opacity:0, 1x1) behind a
  // styled switch — force the check/uncheck since Playwright's
  // actionability check would otherwise wait for "visible" forever.
  await page.getByTestId('scope-toggle-input').check({ force: true })
  await expect
    .poll(async () => Number(await countIndicator.getAttribute('data-count')), { timeout: 10_000 })
    .toBeGreaterThan(defaultCount)

  // Leave it toggled back off for the following tests in this file.
  await page.getByTestId('scope-toggle-input').uncheck({ force: true })
})

test('search filters rows down to the synthetic E2E transactions', async ({ page }) => {
  await page.goto('/records')
  await expect(page.getByTestId('transaction-row').first()).toBeVisible({ timeout: 10_000 })

  await page.getByLabel('Search').fill('E2E TEST ROW')
  await expect
    .poll(async () => page.getByTestId('transaction-row').count(), { timeout: 10_000 })
    .toBe(2)

  const rows = page.getByTestId('transaction-row')
  await expect(rows.nth(0)).toContainText('E2E TEST ROW')
  await expect(rows.nth(1)).toContainText('E2E TEST ROW')

  await page.getByLabel('Search').fill('')
})

test('sorting by amount changes the first row', async ({ page }) => {
  await page.goto('/records')
  await expect(page.getByTestId('transaction-row').first()).toBeVisible({ timeout: 10_000 })

  const firstRowBefore = await page.getByTestId('transaction-row').first().getAttribute('data-description')

  // Default sort is txn_date desc; clicking "Amount" switches to
  // amount desc, which should reorder the top row.
  await page.getByRole('button', { name: 'Amount' }).click()
  await expect
    .poll(async () => page.getByTestId('transaction-row').first().getAttribute('data-description'), {
      timeout: 10_000,
    })
    .not.toBe(firstRowBefore)
})

test('inline recategorize a synthetic E2E transaction and revert it', async ({ page }) => {
  await page.goto('/records')
  await page.getByLabel('Search').fill('E2E TEST ROW ONE')

  const row = page.getByTestId('transaction-row').filter({ hasText: 'E2E TEST ROW ONE' }).first()
  await expect(row).toBeVisible({ timeout: 10_000 })

  const select = row.getByTestId('category-picker-select')
  const originalValue = await select.inputValue() // '' means Uncategorized

  // Pick the first non-"Uncategorized" option.
  const options = await select.locator('option').all()
  let targetValue: string | null = null
  for (const option of options) {
    const value = await option.getAttribute('value')
    if (value && value !== originalValue) {
      targetValue = value
      break
    }
  }
  expect(targetValue).not.toBeNull()

  await select.selectOption(targetValue!)
  await expect(select).toHaveValue(targetValue!)

  // Dismiss the "also add keyword" follow-up if it appears — we don't
  // want to mutate category keyword config from this test.
  const dismiss = row.getByTestId('followup-dismiss')
  if (await dismiss.isVisible().catch(() => false)) {
    await dismiss.click()
  }

  // Revert back to the original category.
  await select.selectOption(originalValue)
  await expect(select).toHaveValue(originalValue)
  const dismissAgain = row.getByTestId('followup-dismiss')
  if (await dismissAgain.isVisible().catch(() => false)) {
    await dismissAgain.click()
  }

  await page.getByLabel('Search').fill('')
})
