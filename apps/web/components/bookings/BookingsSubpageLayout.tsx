'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'
import { LayoutGrid, Pencil, QrCode } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

const TABS = [
  { href: '/dashboard/bookings/widget', label: 'Widget & QR', icon: QrCode },
  { href: '/dashboard/bookings/form-builder', label: 'Form builder', icon: Pencil },
] as const

type Props = {
  tenantName?: string
  userName?: string
  subtitle: string
  children: ReactNode
  maxWidth?: 'md' | 'lg' | 'xl'
}

export function BookingsSubpageLayout({
  tenantName,
  userName,
  subtitle,
  children,
  maxWidth = 'lg',
}: Props) {
  const pathname = usePathname()
  const maxClass =
    maxWidth === 'xl' ? 'max-w-5xl' : maxWidth === 'md' ? 'max-w-2xl' : 'max-w-3xl'

  return (
    <div className={cn('mx-auto w-full px-4 sm:px-6 pb-10', maxClass)}>
      <div className="space-y-6">
        <TenantWelcomeHeader tenantName={tenantName} userName={userName} subtitle={subtitle} />

        <nav
          className="flex flex-wrap items-center gap-2 text-sm"
          aria-label="Bookings tools"
        >
          <Link
            href="/dashboard/bookings"
            className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-brand-teal-100/70 hover:bg-brand-forest-900 hover:text-white transition-colors"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Bookings hub
          </Link>
          {TABS.map(({ href, label, icon: Icon }) => {
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

        <div className="space-y-6">{children}</div>
      </div>
    </div>
  )
}
