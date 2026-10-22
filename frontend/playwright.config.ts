import { defineConfig, devices } from '@playwright/test'

const backendPython = process.env.PYTHON_BACKEND ?? process.env.PYTHON ?? 'python'
const mlPython = process.env.PYTHON_ML ?? process.env.PYTHON ?? 'python'
const backendPort = process.env.E2E_BACKEND_PORT ?? '8000'
const mlPort = process.env.E2E_ML_PORT ?? '8001'
const frontendPort = process.env.E2E_FRONTEND_PORT ?? '5173'

/**
 * End-to-end configuration.
 *
 * Playwright starts the three real services itself:
 *   ML service -> backend API -> Vite dev server.
 *
 * Set PYTHON to the interpreter that has the backend and ML dependencies
 * installed, or set PYTHON_BACKEND and PYTHON_ML separately. On Windows:
 *   $env:PYTHON_BACKEND = "..\\backend\\.venv\\Scripts\\python.exe"
 *   $env:PYTHON_ML = "..\\ml-service\\.venv\\Scripts\\python.exe"
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${mlPython} -m uvicorn app.main:app --host 127.0.0.1 --port ${mlPort}`,
      cwd: '../ml-service',
      url: `http://127.0.0.1:${mlPort}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ML_LOG_LEVEL: 'WARNING',
        ML_ARTIFACT_DIR: '../data/artifacts',
      },
    },
    {
      command: `${backendPython} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: '../backend',
      url: `http://127.0.0.1:${backendPort}/ready`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ENVIRONMENT: 'testing',
        DATABASE_URL: 'sqlite:///./data/e2e.db',
        STORAGE_ROOT: './data/e2e-storage',
        AUTO_CREATE_SCHEMA: 'true',
        ML_SERVICE_URL: `http://127.0.0.1:${mlPort}`,
        AUTH_ENABLED: 'false',
        DEMO_MODE: 'true',
        LOG_LEVEL: 'WARNING',
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
})
