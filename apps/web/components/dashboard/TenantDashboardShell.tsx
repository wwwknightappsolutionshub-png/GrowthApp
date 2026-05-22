'use client'

import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { CrossModuleCharts } from '@/components/dashboard/CrossModuleCharts'
import { LandingPagePromptBanner } from '@/components/dashboard/LandingPagePrompt'
import { auth, tenants } from '@/lib/api-client'

export function TenantDashboardShell({
  roleLabel,
  badgeVariant = 'secondary',
  children,
}: {
  roleLabel: string
  badgeVariant?: 'secondary' | 'default' | 'outline'
  children?: React.ReactNode
}) {
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div className="flex-1 min-w-0">
          <TenantWelcomeHeader tenantName={tenant?.name} userName={me?.full_name} />
        </div>
        <Badge variant={badgeVariant} className="capitalize shrink-0">
          {roleLabel}
        </Badge>
      </div>
      <LandingPagePromptBanner />
      <CrossModuleCharts />
      {children}
    </div>
  )
}
