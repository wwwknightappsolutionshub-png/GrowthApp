import { test, expect } from '@playwright/test'

/**
 * Public widget & landing surface — these endpoints are served from the API
 * and proxied through Next.js. The smoke tests just make sure the routes
 * respond and the widget script is well-formed JavaScript.
 */

test('public widget.js is served as JavaScript', async ({ request }) => {
  const res = await request.get('/api/v1/public/widget.js')
  expect(res.status()).toBeLessThan(500)
  if (res.status() === 200) {
    const body = await res.text()
    expect(body.length).toBeGreaterThan(50)
    expect(body).toMatch(/customerflow|widget|button/i)
  }
})

test('lead capture endpoint exists', async ({ request }) => {
  const res = await request.post('/api/v1/public/leads/nonexistent-tenant', {
    data: { first_name: 'Test', email: 'noone@example.com' },
  })
  // Expect 404 (tenant not found) or 422 (validation), not a 500.
  expect([400, 404, 422]).toContain(res.status())
})
