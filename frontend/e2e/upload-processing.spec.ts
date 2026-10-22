import { test, expect } from '@playwright/test'
import path from 'node:path'

const fixture = path.resolve('e2e/fixtures/synthetic_palm.png')

test.describe('critical research workflow', () => {
  test('upload -> validate -> process -> enhancement result', async ({ page }) => {
    await page.goto('/upload')
    await expect(page.getByRole('heading', { name: 'Upload a palmprint image' })).toBeVisible()

    await page.setInputFiles('input[type="file"]', fixture)
    await expect(page.getByText('synthetic_palm.png')).toBeVisible()

    await page.getByRole('button', { name: 'Upload image' }).click()
    await expect(page.getByRole('heading', { name: 'Uploaded image' })).toBeVisible({
      timeout: 45_000,
    })

    await page.getByRole('button', { name: 'Process this image' }).click()
    await expect(page).toHaveURL(/\/processing\?image=/)
    await expect(page.getByRole('heading', { name: 'Processing' })).toBeVisible()

    // ROI extraction may legitimately fail for a synthetic texture; the
    // application must still return control to the user without a crash.
    await page.getByRole('button', { name: 'Extract ROI' }).click()
    await expect(page.getByRole('button', { name: 'Extract ROI' })).toBeEnabled({
      timeout: 45_000,
    })

    // CLAHE enhancement is deterministic and must always produce a download.
    await page.getByRole('button', { name: 'Apply enhancement' }).click()
    await expect(page.getByRole('link', { name: /Download enhanced/i })).toBeVisible({
      timeout: 45_000,
    })
  })

  test('quality page shows interpretation caveats', async ({ page }) => {
    await page.goto('/quality')
    await expect(
      page.getByText(/combined score is an experimental, unvalidated heuristic/i),
    ).toBeVisible()
  })
})
