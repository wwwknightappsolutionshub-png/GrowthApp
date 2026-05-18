import { test, expect } from '@playwright/test'

/**
 * Public-facing smoke tests.
 *
 * These tests don't require a logged-in session — they exercise the
 * marketing/auth surface so we always know the app boots, the login form
 * renders, and the auth middleware redirects gated routes.
 */

test('home page renders the CustomerFlow AI brand', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/CustomerFlow AI/i)
})

test('login page renders the form', async ({ page }) => {
  await page.goto('/login')
  await expect(
    page.getByRole('textbox', { name: /email/i }).first(),
  ).toBeVisible()
  await expect(
    page.getByRole('button', { name: /sign in|log in|continue/i }).first(),
  ).toBeVisible()
})

test('register page renders the form', async ({ page }) => {
  await page.goto('/register')
  await expect(
    page.getByRole('textbox').first(),
  ).toBeVisible()
})

test('dashboard redirects unauthenticated visitors to /login', async ({ page }) => {
  const response = await page.goto('/dashboard', { waitUntil: 'load' })
  // The Next.js middleware redirects 302 → /login; the final URL should be the login page.
  expect(page.url()).toMatch(/\/login(\?|$)/)
  // Status of the final document should still be 200.
  expect(response?.status() ?? 0).toBeLessThan(400)
})
