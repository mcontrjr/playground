import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * Crafted fixture: a valid Citi header + 2 good synthetic rows + 1
 * broken row (garbage date -> per-row fault isolation surfaces it as
 * a RowFailure instead of aborting the whole batch).
 *
 * The 2 good rows are intentionally fake and tiny so they don't
 * pollute real analytics meaningfully if left in the dev DB after the
 * suite runs:
 *   - descriptions: "E2E TEST ROW ONE" / "E2E TEST ROW TWO" (clearly synthetic)
 *   - amount: $0.01 each (negligible)
 *   - dated 2020-01-15/16, well outside the real 2026 statement range
 * This spec marks the resulting failure resolved as its last step, but
 * intentionally leaves the 2 good rows in the DB per the test plan —
 * they're used again by records.spec.ts to exercise recategorization.
 */

const FIXTURE = path.resolve(__dirname, './fixtures/citi_e2e_failures.csv')

test('malformed row is isolated as a failure; good rows still ingest', async ({ page }) => {
  await page.goto('/upload')

  await page.getByTestId('upload-file-input').setInputFiles(FIXTURE)

  const result = page.getByTestId('upload-result').first()
  await expect(result).toBeVisible({ timeout: 15_000 })

  // The 2 good synthetic rows dedupe by content hash on any rerun of
  // this spec (e.g. a second suite run against the same dev DB), so
  // "inserted" is 2 only the first time and 0 on subsequent runs —
  // either way inserted + duplicates must equal 2. The malformed row
  // is never persisted (it has no content hash), so it always reports
  // as exactly 1 fresh failure per run.
  const insertedText = await result.getByTestId('upload-result-inserted').textContent()
  const duplicatesText = await result.getByTestId('upload-result-duplicates').textContent()
  expect(Number(insertedText) + Number(duplicatesText)).toBe(2)
  await expect(result.getByTestId('upload-result-failures')).toHaveText('1')

  const failureRow = result.getByTestId('failure-row').first()
  await expect(failureRow).toBeVisible()
  await expect(failureRow.getByTestId('failure-line-number')).toHaveText('#3')
  await expect(failureRow.getByTestId('failure-raw-line')).toContainText('NOT-A-DATE')
  await expect(failureRow.getByTestId('failure-raw-line')).toContainText('E2E TEST ROW BROKEN')

  await failureRow.getByTestId('failure-resolve-button').click()
  await expect(failureRow.getByTestId('failure-resolved')).toBeVisible()
})
