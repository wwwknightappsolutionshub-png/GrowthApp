import { test, expect } from '@playwright/test'

/**
 * Login form interaction smoke test. Doesn't actually authenticate (that would
 * need a seeded test tenant), but verifies the form fires the expected request.
 */

test('login form submits credentials to the API', async ({ page }) => {
  await page.goto('/login')

  const apiRequest = page.waitForRequest(
    (req) => req.url().includes('/api/v1/auth/login') && req.method() === 'POST',
  )

  const email = page.getByRole('textbox', { name: /email/i }).first()
  await email.fill('test@example.com')

  const password = page.locator('input[type="password"]').first()
  await password.fill('correct horse battery staple')

  await page.getByRole('button', { name: /sign in|log in|continue/i }).first().click()

  const req = await apiRequest
  expect(req.postDataJSON()).toMatchObject({ email: 'test@example.com' })
})

test('forgot password page renders', async ({ page }) => {
  await page.goto('/forgot-password')
  await expect(page.getByRole('textbox', { name: /email/i }).first()).toBeVisible()
})
