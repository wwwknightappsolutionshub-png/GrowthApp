'use client'

import { Menu, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { tenants } from '@/lib/api-client'
import { getInitials } from '@/lib/utils'
import { NotificationBell } from '@/components/notifications/NotificationBell'
import { ThemeToggle } from '@/components/theme-toggle'
import { useCommandPalette } from '@/lib/stores/command-palette'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

interface TopBarProps {
  title?: string
  onMenuClick?: () => void
}

export function TopBar({ title, onMenuClick }: TopBarProps) {
  const { data: tenantData } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  })
  const openPalette = useCommandPalette((s) => s.open)

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-background/85 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/70 sm:px-6">
      {/* Page title slot */}
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-muted/50 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
            aria-label="Open navigation"
          >
            <Menu className="h-4 w-4" />
          </button>
        )}
        {title && (
          <h1 className="font-display text-lg font-semibold tracking-tight text-foreground">
            {title}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Command palette */}
        <button
          type="button"
          onClick={openPalette}
          className="group inline-flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-foreground/20 hover:bg-muted hover:text-foreground"
          aria-label="Open command palette"
        >
          <Search className="h-4 w-4" />
          <span className="hidden md:inline">Search anything</span>
          <kbd className="ml-1 hidden rounded border border-border bg-background px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground md:inline">
            ⌘K
          </kbd>
        </button>

        <ThemeToggle />
        <NotificationBell />

        {/* Tenant identity */}
        <div className="ml-1 flex items-center gap-2.5 border-l border-border pl-3">
          <Avatar className="h-8 w-8 ring-1 ring-border">
            <AvatarFallback className="bg-brand-forest-700 font-mono text-[11px] font-bold uppercase tracking-wider text-brand-forest-foreground">
              {tenantData ? getInitials(tenantData.name) : '?'}
            </AvatarFallback>
          </Avatar>
          {tenantData && (
            <div className="hidden flex-col leading-tight sm:flex">
              <span className="max-w-[160px] truncate text-sm font-semibold text-foreground">
                {tenantData.name}
              </span>
              <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                Workspace
              </span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
