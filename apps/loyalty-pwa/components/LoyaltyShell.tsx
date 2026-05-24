'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Gift, History, Home, QrCode, User, Users } from 'lucide-react'
import clsx from 'clsx'
import { LoyaltyNotificationBell } from '@/components/LoyaltyNotificationBell'
import { useBranding } from '@/components/BrandingProvider'

const NAV = [
  { href: 'dashboard', label: 'Home', icon: Home },
  { href: 'rewards', label: 'Rewards', icon: Gift },
  { href: 'refer', label: 'Refer', icon: Users },
  { href: 'history', label: 'History', icon: History },
  { href: 'qr', label: 'QR', icon: QrCode },
  { href: 'profile', label: 'Profile', icon: User },
] as const

export function LoyaltyShell({ tenant, children }: { tenant: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const { branding } = useBranding()
  const hideNav = pathname.includes('/login') || pathname.includes('/auth/')

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col">
      <header className="wallet-header sticky top-0 z-10 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          {branding?.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={branding.logo_url}
              alt=""
              className="h-9 w-9 rounded-full border-2 border-white/30 object-cover"
            />
          ) : (
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-white/25 bg-white/15 text-sm font-bold text-white">
              {(branding?.tenant_name ?? tenant).slice(0, 1).toUpperCase()}
            </div>
          )}
          <div>
            <p className="text-sm font-semibold text-white">{branding?.tenant_name ?? 'Rewards'}</p>
            <p className="text-xs text-white/75">Member wallet</p>
          </div>
          <LoyaltyNotificationBell tenant={tenant} />
        </div>
      </header>

      <main className="flex-1 px-4 py-4 pb-24">{children}</main>

      {!hideNav ? (
        <nav className="wallet-nav fixed bottom-0 left-0 right-0 z-10 border-t backdrop-blur">
          <div className="mx-auto flex max-w-lg justify-around px-1 py-2">
            {NAV.map(({ href, label, icon: Icon }) => {
              const path = `/${tenant}/${href}`
              const active = pathname === path || pathname.startsWith(`${path}/`)
              return (
                <Link
                  key={href}
                  href={path}
                  className={clsx(
                    'flex flex-col items-center gap-0.5 rounded-lg px-1.5 py-1.5 text-[10px] font-medium transition-colors',
                    active ? 'wallet-nav-link-active' : 'text-muted',
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {label}
                </Link>
              )
            })}
          </div>
        </nav>
      ) : null}
    </div>
  )
}
