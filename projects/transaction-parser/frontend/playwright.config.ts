import { defineConfig, devices } from '@playwright/test'

/**
 * E2E suite against the already-running docker-compose stack
 * (frontend on :5174, backend on :58000). These tests do not start
 * their own servers — `docker compose up` must already be running.
 *
 * System chromium is used instead of a Playwright-managed download
 * because `npx playwright install` requires root in this environment.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    launchOptions: {
      executablePath: '/usr/bin/chromium',
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
