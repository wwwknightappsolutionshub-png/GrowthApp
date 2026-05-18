import { expect, test } from '@playwright/test'

test.use({ viewport: { width: 390, height: 844 }, isMobile: true })
test.setTimeout(90_000)

test('marketing mobile menu exposes primary navigation', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 90_000 })

  await page.getByRole('button', { name: /open menu/i }).click()
  const mobileMenu = page.locator('header details[open]')
  await expect(mobileMenu.getByRole('link', { name: 'Platform' })).toBeVisible()
  await expect(mobileMenu.getByRole('link', { name: 'Pricing' })).toBeVisible()
  await expect(page.getByRole('banner').getByRole('link', { name: /start free trial/i })).toBeVisible()
})

test('authenticated routes redirect cleanly on mobile viewport', async ({ page }) => {
  await page.goto('/dashboard', { waitUntil: 'domcontentloaded', timeout: 90_000 })
  await expect(page).toHaveURL(/\/login(\?|$)/)
})
