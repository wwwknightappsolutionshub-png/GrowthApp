'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  Building2,
  Download,
  LayoutDashboard,
  Settings,
  Target,
  UserCircle,
  Users,
} from 'lucide-react'
import { auth, crm, tenants } from '@/lib/api-client'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { ModuleCardGrid, type ModuleCardItem } from '@/components/modules/ModuleCardGrid'
import { CrmEducatorPanel } from '@/components/crm/CrmEducatorPanel'

export default function CrmHubPage() {
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })
  const { data: dash } = useQuery({
    queryKey: ['crm', 'dashboard'],
    queryFn: () => crm.dashboard().then((r) => r.data),
  })

  const tiles: ModuleCardItem[] = [
    {
      title: 'Pipeline',
      description: 'Unified board — drag deals across stages.',
      href: '/dashboard/crm/board',
      icon: Target,
    },
    {
      title: 'Customers',
      description: 'Enterprise profiles, visits, follow-ups, and custom fields.',
      href: '/dashboard/crm/customers',
      icon: Users,
    },
    {
      title: 'Segments',
      description: 'Rule-based groups for campaigns and outreach.',
      href: '/dashboard/crm/segments',
      icon: UserCircle,
    },
    {
      title: 'Import',
      description: 'Bulk import contacts and deals from CSV.',
      href: '/dashboard/crm/import',
      icon: Download,
    },
    {
      title: 'Company profile',
      description: 'Business clients — name, phone, address, contract.',
      href: '/dashboard/crm/companies',
      icon: Building2,
    },
    {
      title: 'Settings',
      description: 'Pipelines, stages, fields, and automation hooks.',
      href: '/dashboard/crm/settings',
      icon: Settings,
    },
  ]

  const kpi = [
    { label: 'New leads today', value: dash?.new_leads_today ?? 0 },
    { label: 'Deals won (month)', value: dash?.deals_won_this_month ?? 0 },
    {
      label: 'Pipeline value',
      value: dash?.total_pipeline_value_pence != null
        ? `£${(dash.total_pipeline_value_pence / 100).toLocaleString('en-GB')}`
        : '—',
    },
    { label: 'Lead sources', value: Object.keys(dash?.leads_by_source ?? {}).length || '—' },
  ]

  return (
    <div className="space-y-6">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="CRM — pipeline, customers, and revenue operations"
      />

      <section className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-5">
        <div className="flex items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <LayoutDashboard className="w-5 h-5 text-brand-teal-300" />
            CRM dashboard
          </h2>
          <Link
            href="/dashboard/crm/dashboard"
            className="text-xs font-semibold text-brand-teal-300 hover:text-brand-teal-200"
          >
            Full dashboard →
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {kpi.map((w) => (
            <div
              key={w.label}
              className="rounded-xl border border-brand-forest-800 bg-brand-forest-900 p-4"
            >
              <p className="text-[10px] uppercase font-bold text-brand-teal-100/60">{w.label}</p>
              <p className="text-xl font-black text-white mt-1">{w.value}</p>
            </div>
          ))}
        </div>
      </section>

      <CrmEducatorPanel />

      <div>
        <h2 className="text-sm font-bold text-white mb-3">CRM tools</h2>
        <ModuleCardGrid items={tiles} />
      </div>
    </div>
  )
}
