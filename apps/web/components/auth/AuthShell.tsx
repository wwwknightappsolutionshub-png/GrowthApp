'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { AuthJourneyHeadline } from '@/components/brand/AuthJourneyHeadline'
import { BrandMark } from '@/components/brand/BrandMark'

const AUTH_BACKGROUNDS: Record<string, string> = {
  '/login':
    'https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
  '/register':
    'https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
  '/forgot-password':
    'https://images.pexels.com/photos/6052192/pexels-photo-6052192.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
}

const AUTH_BADGES: Record<string, string> = {
  '/login': 'Welcome back',
  '/register': 'Start your free trial',
  '/forgot-password': 'Secure account recovery',
}

const DEFAULT_BACKGROUND = AUTH_BACKGROUNDS['/login']

function resolveAuthRoute(pathname: string | null) {
  if (!pathname) return '/login'
  if (pathname.startsWith('/register')) return '/register'
  if (pathname.startsWith('/forgot-password')) return '/forgot-password'
  if (pathname.startsWith('/login')) return '/login'
  return '/login'
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const route = resolveAuthRoute(pathname)
  const background = AUTH_BACKGROUNDS[route] ?? DEFAULT_BACKGROUND
  const badge = AUTH_BADGES[route] ?? 'CustomerFlowai'

  return (
    <div className="surface-light flex min-h-screen bg-background">
      <aside className="relative hidden flex-col overflow-hidden bg-brand-forest-950 text-brand-forest-foreground lg:flex lg:w-[44%] xl:w-[40%]">
        <div
          aria-hidden
          className="absolute inset-0 bg-cover bg-center transition-[background-image] duration-700"
          style={{ backgroundImage: `url('${background}')` }}
        />
        <div aria-hidden className="absolute inset-0 bg-brand-forest-950/65" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_100%,hsl(var(--brand-forest)/0.6),transparent_80%)]"
        />

        <div className="relative flex h-full flex-col px-10 py-10">
          <Link href="/" aria-label="CustomerFlowai home">
            <BrandMark variant="light" iconSize={36} textClassName="text-lg" />
          </Link>

          <div className="mt-16 flex flex-1 flex-col justify-center">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-brand-teal-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-teal-300 opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-teal-300" />
              </span>
              {badge}
            </span>

            <h2 className="mt-6 text-3xl xl:text-[40px]">
              <AuthJourneyHeadline lineClassName="text-3xl xl:text-[40px] leading-[1.08]" />
            </h2>
            <p className="mt-5 max-w-md text-base leading-relaxed text-white/80">
              Give customers a rewards wallet on their phone, then run leads, bookings, CRM and
              invoices from one connected workspace.
            </p>
          </div>
        </div>
      </aside>

      <main className="flex flex-1 flex-col bg-background">
        <div className="flex items-center gap-2.5 border-b border-border px-6 py-5 lg:hidden">
          <Link href="/" aria-label="CustomerFlowai home">
            <BrandMark iconSize={32} />
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 py-10">
          <div className="w-full max-w-md">{children}</div>
        </div>

        <footer className="flex flex-col items-center justify-between gap-2 border-t border-border px-6 py-5 sm:flex-row">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            © {new Date().getFullYear()} CustomerFlowai · All rights reserved
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link href="/privacy" className="transition-colors hover:text-foreground">
              Privacy
            </Link>
            <Link href="#" className="transition-colors hover:text-foreground">
              Terms
            </Link>
            <Link href="#" className="transition-colors hover:text-foreground">
              Support
            </Link>
          </div>
        </footer>
      </main>
    </div>
  )
}
