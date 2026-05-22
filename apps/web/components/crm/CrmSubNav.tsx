'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  BarChart3,
  Building2,
  Columns3,
  Download,
  Filter,
  LayoutGrid,
  Settings,
  Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const LINKS = [
  { href: '/dashboard/crm', label: 'Hub', icon: LayoutGrid, exactHub: true },
  { href: '/dashboard/crm/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/dashboard/crm/board', label: 'Pipeline', icon: Columns3 },
  { href: '/dashboard/crm/customers', label: 'Customers', icon: Users },
  { href: '/dashboard/crm/companies', label: 'Companies', icon: Building2 },
  { href: '/dashboard/crm/segments', label: 'Segments', icon: Filter },
  { href: '/dashboard/crm/import', label: 'Import', icon: Download },
  { href: '/dashboard/crm/settings', label: 'Settings', icon: Settings },
]

export function CrmSubNav() {
  const pathname = usePathname()

  return (
    <nav className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-muted/40 p-1">
      {LINKS.map(({ href, label, icon: Icon, ...rest }) => {
        const exactHub = 'exactHub' in rest && rest.exactHub
        const active = exactHub
          ? pathname === href
          : pathname === href || pathname.startsWith(`${href}/`)
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              'inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              active
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
