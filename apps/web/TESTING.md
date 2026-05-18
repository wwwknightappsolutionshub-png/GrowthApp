# Frontend testing — CustomerFlow AI Web

Two test layers run in `apps/web`:

| Layer | Tooling | Where |
|---|---|---|
| Unit / component | [Vitest](https://vitest.dev) + [Testing Library](https://testing-library.com) | `**/*.test.ts(x)` co-located with source |
| End-to-end | [Playwright](https://playwright.dev) | `e2e/*.spec.ts` |

## Unit & component tests

```bash
pnpm test            # run once (CI mode)
pnpm test:watch      # watch mode
pnpm test:ui         # browser UI
pnpm test:coverage   # generate ./coverage report
```

Vitest is configured with:

- `jsdom` environment for DOM APIs
- `@testing-library/jest-dom` matchers (`.toBeInTheDocument()` etc.)
- `next/navigation` mocked at the top level so client components that read
  `usePathname()` don't crash in tests
- `matchMedia` + `IntersectionObserver` polyfills (used by `next-themes`,
  Radix, Framer Motion)

Write tests next to the file they cover, with a `.test.ts(x)` suffix.

## End-to-end tests

```bash
# First-time setup — install browsers
npx playwright install --with-deps

# Run everything (auto-starts `pnpm dev`)
pnpm test:e2e

# Run with the UI runner
pnpm test:e2e:ui
```

Playwright auto-starts the Next.js dev server via the `webServer` config.
Set `PLAYWRIGHT_NO_SERVER=1` if you already have it running, or
`PLAYWRIGHT_BASE_URL=…` to point at a deployed environment.

The `e2e/` suite currently covers:

- App boots and serves the home page
- Login / register forms render
- Auth middleware redirects gated `/dashboard` traffic to `/login`
- The login form fires the expected `/api/v1/auth/login` request
- Public widget JS endpoint responds with code
- Public lead capture endpoint validates input

## CI

```yaml
- run: pnpm install
- run: pnpm test            # Vitest
- run: npx playwright install --with-deps chromium
- run: pnpm test:e2e        # Playwright
```
