import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * The dev DB already contains the amex_90_day.csv sample (ingested
 * during earlier phases). Re-uploading it through the UI must be a
 * pure no-op: idempotency via content_hash + occurrence_index means
 * every row dedupes and nothing new is inserted. This also exercises
 * the plain (non-ambiguous) upload path end-to-end.
 */

const FIXTURE = path.resolve(__dirname, '../../transactions/amex_90_day.csv')

test('re-uploading amex_90_day.csv is a no-op (0 inserted, 105 duplicates, 0 failures)', async ({ page }) => {
  await page.goto('/upload')

  const fileInput = page.getByTestId('upload-file-input')
  await fileInput.setInputFiles(FIXTURE)

  const result = page.getByTestId('upload-result').first()
  await expect(result).toBeVisible({ timeout: 15_000 })

  await expect(result.getByTestId('upload-result-inserted')).toHaveText('0')
  await expect(result.getByTestId('upload-result-duplicates')).toHaveText('105')
  await expect(result.getByTestId('upload-result-failures')).toHaveText('0')

  // The batch should also appear in the recent-batches history.
  const batchRow = page.getByTestId('batch-row').filter({ hasText: 'amex_90_day.csv' }).first()
  await expect(batchRow).toBeVisible()
})
