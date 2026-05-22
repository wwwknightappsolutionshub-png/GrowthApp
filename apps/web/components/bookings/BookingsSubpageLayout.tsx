'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'
import { CalendarPlus, LayoutGrid, Pencil, QrCode } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

export const BOOKINGS_SUBNAV = [
  { href: '/dashboard/bookings/new', label: 'New booking', icon: CalendarPlus },
  { href: '/dashboard/bookings/widget', label: 'Widget & QR', icon: QrCode },
  { href: '/dashboard/bookings/form-builder', label: 'Form builder', icon: Pencil },
] as const

/** Shared max width for bookings subpages (centered in dashboard main). */
export const BOOKINGS_TOOLS_MAX_W = 'max-w-3xl'

type Props = {
  tenantName?: string
  userName?: string
  subtitle: string
  children: ReactNode
}

export function BookingsPanel({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <section
      className={cn(
        'w-full rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6 sm:p-8 shadow-sm',
        className,
      )}
    >
      {children}
    </section>
  )
}

export function BookingsSubpageLayout({ tenantName, userName, subtitle, children }: Props) {
  const pathname = usePathname()

  return (
    <div className="flex w-full justify-center">
      <div className={cn('w-full px-1 sm:px-2 pb-10', BOOKINGS_TOOLS_MAX_W)}>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="w-full">
            <TenantWelcomeHeader
              tenantName={tenantName}
              userName={userName}
              subtitle={subtitle}
              centered
            />
          </div>

          <nav
            className="flex flex-wrap items-center justify-center gap-2 text-sm w-full"
            aria-label="Bookings tools"
          >
            <Link
              href="/dashboard/bookings"
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-brand-teal-100/70 hover:bg-brand-forest-900 hover:text-white transition-colors"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              Bookings hub
            </Link>
            {BOOKINGS_SUBNAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition-colors',
                    active
                      ? 'bg-brand-teal-600/25 text-white ring-1 ring-brand-teal-500/40'
                      : 'text-brand-teal-100/70 hover:bg-brand-forest-900 hover:text-white',
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </Link>
              )
            })}
          </nav>

          <div className="w-full flex flex-col items-center gap-6 text-left">{children}</div>
        </div>
      </div>
    </div>
  )
}
