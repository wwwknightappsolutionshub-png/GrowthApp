'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Gift, History, Home, QrCode, User } from 'lucide-react'
import clsx from 'clsx'
import { useLoyaltyBranding } from '@/components/loyalty-portal/LoyaltyBrandingProvider'
import { rewardsPath } from '@/lib/loyalty-portal-auth'

const NAV = [
  { href: 'dashboard', label: 'Home', icon: Home },
  { href: 'rewards', label: 'Rewards', icon: Gift },
  { href: 'history', label: 'History', icon: History },
  { href: 'qr', label: 'QR', icon: QrCode },
  { href: 'profile', label: 'Profile', icon: User },
] as const

export function LoyaltyPortalShell({ tenant, children }: { tenant: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const { branding } = useLoyaltyBranding()
  const hideNav = pathname.includes('/login') || pathname.includes('/auth/')

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          {branding?.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={branding.logo_url} alt="" className="h-8 w-8 rounded-full object-cover" />
          ) : (
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white"
              style={{ backgroundColor: 'var(--tenant-primary)' }}
            >
              {(branding?.tenant_name ?? tenant).slice(0, 1).toUpperCase()}
            </div>
          )}
          <div>
            <p className="text-sm font-semibold">{branding?.tenant_name ?? 'Rewards'}</p>
            <p className="text-xs text-slate-500">Member wallet</p>
          </div>
        </div>
      </header>

      <main className="flex-1 px-4 py-4 pb-24">{children}</main>

      {!hideNav ? (
        <nav className="fixed bottom-0 left-0 right-0 z-10 border-t border-slate-200 bg-white">
          <div className="mx-auto flex max-w-lg justify-around px-2 py-2">
            {NAV.map(({ href, label, icon: Icon }) => {
              const path = rewardsPath(tenant, href)
              const active = pathname === path || pathname.startsWith(`${path}/`)
              return (
                <Link
                  key={href}
                  href={path}
                  className={clsx(
                    'flex flex-col items-center gap-0.5 rounded-lg px-2 py-1.5 text-[10px] font-medium',
                    active ? 'text-[var(--tenant-primary)]' : 'text-slate-500',
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
