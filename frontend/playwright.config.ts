import { defineConfig, devices } from '@playwright/test'

const FRONTEND_PORT = Number(process.env.E2E_FRONTEND_PORT ?? 3055)
const BACKEND_PORT = Number(process.env.E2E_BACKEND_PORT ?? 8055)
const E2E_WORKSPACE = process.env.E2E_WORKSPACE_DIR ?? '/tmp/portaible-e2e-workspace'

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,            // single backend, single workspace — keep serial
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],

  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: [
    {
      // Backend (FastAPI) — points at an isolated workspace + DB and uses the
      // Fake analyzer/decisions adapters so we don't need Ollama in CI/dev.
      command: `bash -c "rm -rf ${E2E_WORKSPACE} && uv run uvicorn portaible.app:app --host 127.0.0.1 --port ${BACKEND_PORT}"`,
      cwd: '..',
      env: {
        WORKSPACE_DIR: E2E_WORKSPACE,
        DATABASE_URL: `sqlite+aiosqlite:///${E2E_WORKSPACE}/e2e.db`,
        USE_FAKE_ANALYZER: 'true',
        AI_PIPELINE_URL: 'http://localhost:9999',     // unused by happy-path spec
        FRONTEND_ORIGIN: `http://127.0.0.1:${FRONTEND_PORT}`,
        LOG_LEVEL: 'WARNING',
      },
      url: `http://127.0.0.1:${BACKEND_PORT}/api/health`,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      // Frontend (Nuxt) — points at the test backend.
      command: `npx nuxt dev --port ${FRONTEND_PORT} --host 127.0.0.1`,
      env: {
        NUXT_PUBLIC_API_BASE: `http://127.0.0.1:${BACKEND_PORT}`,
        NUXT_IGNORE_LOCK: '1',
      },
      url: `http://127.0.0.1:${FRONTEND_PORT}`,
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
