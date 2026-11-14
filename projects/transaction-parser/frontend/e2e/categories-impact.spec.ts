import { test, expect } from '@playwright/test'

/**
 * Exercises the Categories page lifecycle end-to-end using a fully
 * disposable category ("E2E TEMP") so nothing here touches real data:
 * create -> add keyword (impact preview) -> rename -> delete -> gone.
 * Also asserts the system category "Payments & Transfers" has no
 * delete affordance.
 */

const CATEGORY_NAME = 'E2E TEMP'
const RENAMED_NAME = 'E2E TEMP RENAMED'
const KEYWORD = 'E2E-TEMP-KEYWORD'
const API_BASE = 'http://localhost:58000/api/v1'

test.describe.configure({ mode: 'serial' })

/** Deletes any leftover "E2E TEMP" / "E2E TEMP RENAMED" category from a
 * prior interrupted run via direct API calls, so this spec is
 * idempotent across retries without depending on the UI working. */
async function cleanupLeftoverCategory(request: import('@playwright/test').APIRequestContext) {
  const response = await request.get(`${API_BASE}/categories`)
  if (!response.ok()) return
  const categories: Array<{ id: number; name: string }> = await response.json()
  for (const name of [CATEGORY_NAME, RENAMED_NAME]) {
    const match = categories.find((c) => c.name === name)
    if (match) await request.delete(`${API_BASE}/categories/${match.id}`)
  }
}

test.beforeAll(async ({ request }) => {
  await cleanupLeftoverCategory(request)
})

test.afterAll(async ({ request }) => {
  await cleanupLeftoverCategory(request)
})

test('create, edit, and delete a disposable category', async ({ page }) => {
  await page.goto('/categories')
  await expect(page.getByTestId('category-row').first()).toBeVisible({ timeout: 10_000 })

  // --- create ---
  await page.getByTestId('open-add-category').click()
  await page.getByTestId('new-category-name-input').fill(CATEGORY_NAME)
  await page.getByTestId('submit-create-category').click()

  // Note: the category name lives inside an <input value>, not text
  // content, so `.filter({ hasText })` can't see it — match on the
  // `data-category-name` attribute set by CategoriesPage instead.
  const row = page.locator(`[data-testid="category-row"][data-category-name="${CATEGORY_NAME}"]`)
  await expect(row).toBeVisible({ timeout: 10_000 })

  // --- add keyword via impact preview ---
  await row.getByTestId('add-keyword-input').fill(KEYWORD)
  await row.getByTestId('add-keyword-submit').click()

  const impactDialog = page.getByRole('dialog', { name: 'Keyword impact preview' })
  await expect(impactDialog).toBeVisible({ timeout: 10_000 })
  await expect(impactDialog.getByTestId('impact-affected-count')).toBeVisible()
  // Breakdown table only renders when affected_count > 0; a brand new
  // disposable keyword typically affects zero transactions, so just
  // assert the count renders a number (0 is a valid, expected result).
  const affectedCount = Number(await impactDialog.getByTestId('impact-affected-count').getAttribute('data-count'))
  expect(affectedCount).toBeGreaterThanOrEqual(0)

  await impactDialog.getByTestId('impact-preview-confirm').click()
  await expect(impactDialog).not.toBeVisible()

  await expect(page.getByTestId('categories-toast')).toContainText('Added')

  // --- rename ---
  // `row` is a literal `[data-category-name="E2E TEMP"]` selector, so it
  // stops matching the moment the attribute changes to the renamed
  // value — re-locate by the new name rather than reusing it.
  const nameInput = row.getByTestId('category-name-input')
  await nameInput.fill(RENAMED_NAME)
  await nameInput.blur()

  await expect(page.getByTestId('categories-toast')).toContainText('Renamed')
  const renamedRow = page.locator(`[data-testid="category-row"][data-category-name="${RENAMED_NAME}"]`)
  await expect(renamedRow).toBeVisible({ timeout: 10_000 })

  // --- delete ---
  await renamedRow.getByTestId('category-delete-button').click()
  const confirmDialog = page.getByRole('dialog', { name: 'Confirm delete category' })
  await expect(confirmDialog).toBeVisible()
  await confirmDialog.getByTestId('confirm-delete-category').click()

  await expect(page.getByTestId('categories-toast')).toContainText('Deleted')
  await expect(page.locator(`[data-testid="category-row"][data-category-name="${RENAMED_NAME}"]`)).toHaveCount(0)
})

test('system category "Payments & Transfers" has no delete affordance', async ({ page }) => {
  await page.goto('/categories')
  const systemRow = page.locator('[data-testid="category-row"][data-category-name="Payments & Transfers"]')
  await expect(systemRow).toBeVisible({ timeout: 10_000 })
  await expect(systemRow.getByTestId('category-delete-button')).toHaveCount(0)
})
