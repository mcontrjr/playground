import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * Capital One and Discover share an identical CSV header, so detection
 * falls back to a filename substring tiebreak (see
 * backend/app/parsers/registry.py). Naming the file "export.csv" (no
 * "capital"/"discover" hint) forces the 409 AMBIGUOUS_INSTITUTION path
 * and the institution-picker dialog.
 *
 * The fixture is a temp copy of the real capital_one_since_sept.csv
 * fixture (already in the dev DB), so after picking "Capital One" all
 * 122 rows dedupe — nothing new is written.
 */

const SOURCE = path.resolve(__dirname, '../../transactions/capital_one_since_sept.csv')
const AMBIGUOUS_COPY = path.resolve(__dirname, './fixtures/export.csv')

test.beforeAll(() => {
  fs.mkdirSync(path.dirname(AMBIGUOUS_COPY), { recursive: true })
  fs.copyFileSync(SOURCE, AMBIGUOUS_COPY)
})

test.afterAll(() => {
  fs.rmSync(AMBIGUOUS_COPY, { force: true })
})

test('ambiguous CapOne/Discover filename triggers the institution picker', async ({ page }) => {
  await page.goto('/upload')

  await page.getByTestId('upload-file-input').setInputFiles(AMBIGUOUS_COPY)

  const dialog = page.getByTestId('institution-picker-dialog')
  await expect(dialog).toBeVisible({ timeout: 15_000 })
  await expect(dialog.getByTestId('institution-option-capital_one')).toBeVisible()
  await expect(dialog.getByTestId('institution-option-discover')).toBeVisible()

  await dialog.getByTestId('institution-option-capital_one').click()
  await dialog.getByTestId('institution-picker-confirm').click()

  await expect(dialog).not.toBeVisible()

  const result = page.getByTestId('upload-result').first()
  await expect(result).toBeVisible({ timeout: 15_000 })
  await expect(result.getByTestId('upload-result-inserted')).toHaveText('0')
  await expect(result.getByTestId('upload-result-duplicates')).toHaveText('122')
  await expect(result.getByTestId('upload-result-failures')).toHaveText('0')
})
