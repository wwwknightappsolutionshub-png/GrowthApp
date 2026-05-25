'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Plug, RefreshCw, Search } from 'lucide-react'
import { admin } from '@/lib/api-client'

interface IntegrationsOnboarding {
  google_connected: boolean
  social_connected: boolean
  skipped: boolean
}

interface SocialPlatform {
  channel_type: string
  status: string
  connected_at: string | null
  last_webhook_at: string | null
}

interface TenantGoogle {
  platform_connected: boolean
  platform_location_title: string | null
  platform_last_sync_at: string | null
  credentials_registered: boolean
  credentials_status: string | null
  credentials_expires_at: string | null
  review_count: number
  last_sync_at: string | null
  last_sync_type: string | null
  last_sync_status: string | null
}

interface TenantSocial {
  channels_provisioned: number
  channels_connected: number
  platforms: SocialPlatform[]
  last_webhook_at: string | null
  last_webhook_status: string | null
  webhook_failures_7d: number
}

interface TenantRow {
  tenant_id: string
  tenant_name: string
  tenant_slug: string
  is_active: boolean
  integrations_onboarding: IntegrationsOnboarding
  google: TenantGoogle
  social: TenantSocial
  health_flags: string[]
}

interface OverviewTotals {
  tenants_total: number
  tenants_with_google_platform: number
  tenants_with_google_credentials: number
  tenants_with_any_social_channel: number
  tenants_with_connected_social: number
  onboarding_skipped: number
  google_sync_failures_24h: number
  social_webhook_failures_24h: number
}

interface OverviewResponse {
  totals: OverviewTotals
  tenants: TenantRow[]
}

type FilterMode = 'all' | 'connected' | 'issues'

const FLAG_LABELS: Record<string, string> = {
  onboarding_google_mismatch: 'Onboarding says Google connected, but no OAuth row',
  onboarding_social_mismatch: 'Onboarding says social connected, but no live channel',
  google_platform_no_location: 'Google OAuth started — location not selected',
  google_credentials_expired: 'Tenant Google token expired',
  google_token_expiring: 'Tenant Google token expiring within 24h',
  social_pending: 'Social channel awaiting first webhook',
  google_sync_failed: 'Last Google sync failed',
  social_webhook_failures: 'Social webhook failures in last 7 days',
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function googleStatus(row: TenantRow): { label: string; tone: 'green' | 'amber' | 'gray' | 'red' } {
  const { google: g } = row
  if (g.platform_connected) {
    return { label: 'Platform connected', tone: 'green' }
  }
  if (g.credentials_status === 'connected') {
    return { label: 'Tenant OAuth connected', tone: 'green' }
  }
  if (g.credentials_registered) {
    if (g.credentials_status === 'expired') return { label: 'OAuth expired', tone: 'red' }
    return { label: `OAuth ${g.credentials_status ?? 'pending'}`, tone: 'amber' }
  }
  if (row.integrations_onboarding.google_connected) {
    return { label: 'Onboarding only', tone: 'amber' }
  }
  return { label: 'Not connected', tone: 'gray' }
}

function socialStatus(row: TenantRow): { label: string; tone: 'green' | 'amber' | 'gray' | 'red' } {
  const { social: s } = row
  if (s.channels_connected > 0) {
    return { label: `${s.channels_connected}/${s.channels_provisioned} connected`, tone: 'green' }
  }
  if (s.channels_provisioned > 0) {
    return { label: `${s.channels_provisioned} pending`, tone: 'amber' }
  }
  if (row.integrations_onboarding.social_connected) {
    return { label: 'Onboarding only', tone: 'amber' }
  }
  if (s.webhook_failures_7d > 0) {
    return { label: 'Webhook failures', tone: 'red' }
  }
  return { label: 'None', tone: 'gray' }
}

function badgeClass(tone: 'green' | 'amber' | 'gray' | 'red'): string {
  switch (tone) {
    case 'green':
      return 'bg-green-900/40 text-green-300'
    case 'amber':
      return 'bg-amber-900/40 text-amber-300'
    case 'red':
      return 'bg-red-900/40 text-red-300'
    default:
      return 'bg-gray-800 text-gray-400'
  }
}

export default function AdminIntegrationsPage() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<FilterMode>('all')

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['admin', 'integrations', 'overview'],
    queryFn: () => admin.integrationsOverview().then((r) => r.data as OverviewResponse),
  })

  const totals = data?.totals
  const tenants = data?.tenants ?? []

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return tenants.filter((row) => {
      if (q) {
        const hay = `${row.tenant_name} ${row.tenant_slug}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      if (filter === 'connected') {
        return (
          row.google.platform_connected ||
          row.google.credentials_status === 'connected' ||
          row.social.channels_connected > 0
        )
      }
      if (filter === 'issues') {
        return row.health_flags.length > 0
      }
      return true
    })
  }, [tenants, search, filter])

  return (
    <div className="text-white">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Plug className="h-6 w-6 text-amber-400" />
            Integrations Overview
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Read-only view of tenant Google OAuth and Zapier/Make social webhook connections.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        {[
          ['Tenants', totals?.tenants_total ?? 0, 'text-white'],
          ['Google (platform)', totals?.tenants_with_google_platform ?? 0, 'text-green-400'],
          ['Google (tenant OAuth)', totals?.tenants_with_google_credentials ?? 0, 'text-emerald-300'],
          ['Social channels', totals?.tenants_with_any_social_channel ?? 0, 'text-amber-300'],
          ['Social live', totals?.tenants_with_connected_social ?? 0, 'text-green-400'],
          ['Onboarding skipped', totals?.onboarding_skipped ?? 0, 'text-gray-400'],
          ['Google sync fails (24h)', totals?.google_sync_failures_24h ?? 0, 'text-red-400'],
          ['Webhook fails (24h)', totals?.social_webhook_failures_24h ?? 0, 'text-red-400'],
        ].map(([label, val, color]) => (
          <div key={label as string} className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="text-[10px] uppercase tracking-wider text-gray-500">{label as string}</div>
            <div className={`mt-1 text-2xl font-bold ${color as string}`}>{val as number}</div>
          </div>
        ))}
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-md flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tenant name or slug…"
            className="w-full rounded-lg border border-gray-800 bg-gray-900 py-2 pl-9 pr-3 text-sm text-white placeholder:text-gray-500 focus:border-amber-500/50 focus:outline-none"
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'connected', 'issues'] as FilterMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setFilter(mode)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition ${
                filter === mode
                  ? 'bg-amber-500 text-black'
                  : 'border border-gray-800 bg-gray-900 text-gray-400 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
        <div className="border-b border-gray-800 px-4 py-3 text-sm font-semibold">
          Tenants ({filtered.length})
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[960px] text-sm">
            <thead className="bg-gray-800/60 text-xs uppercase tracking-wider text-gray-400">
              <tr>
                {[
                  'Tenant',
                  'Google',
                  'Social',
                  'Last Google sync',
                  'Last webhook',
                  'Onboarding',
                  'Flags',
                ].map((h) => (
                  <th key={h} className="px-4 py-3 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    Loading…
                  </td>
                </tr>
              )}
              {!isLoading && filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No tenants match this filter
                  </td>
                </tr>
              )}
              {filtered.map((row) => {
                const g = googleStatus(row)
                const s = socialStatus(row)
                const onboarding = row.integrations_onboarding
                return (
                  <tr key={row.tenant_id} className="hover:bg-gray-800/40">
                    <td className="px-4 py-3">
                      <div className="font-medium">{row.tenant_name}</div>
                      <div className="text-xs text-gray-500">{row.tenant_slug}</div>
                      {!row.is_active && (
                        <span className="mt-1 inline-block rounded bg-gray-800 px-1.5 py-0.5 text-[10px] uppercase text-gray-400">
                          Suspended
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs ${badgeClass(g.tone)}`}>
                        {g.label}
                      </span>
                      {row.google.platform_location_title && (
                        <div className="mt-1 text-xs text-gray-500">{row.google.platform_location_title}</div>
                      )}
                      {row.google.review_count > 0 && (
                        <div className="mt-1 text-xs text-gray-500">{row.google.review_count} reviews cached</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs ${badgeClass(s.tone)}`}>
                        {s.label}
                      </span>
                      {row.social.platforms.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {row.social.platforms.map((p) => (
                            <span
                              key={p.channel_type}
                              className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400"
                            >
                              {p.channel_type}: {p.status}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      <div>{fmtDate(row.google.last_sync_at ?? row.google.platform_last_sync_at)}</div>
                      {row.google.last_sync_type && (
                        <div className="text-gray-500">
                          {row.google.last_sync_type}
                          {row.google.last_sync_status ? ` · ${row.google.last_sync_status}` : ''}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      <div>{fmtDate(row.social.last_webhook_at)}</div>
                      {row.social.last_webhook_status && (
                        <div className="text-gray-500">{row.social.last_webhook_status}</div>
                      )}
                      {row.social.webhook_failures_7d > 0 && (
                        <div className="text-red-400">{row.social.webhook_failures_7d} failures (7d)</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      <div>Google: {onboarding.google_connected ? 'yes' : 'no'}</div>
                      <div>Social: {onboarding.social_connected ? 'yes' : 'no'}</div>
                      {onboarding.skipped && <div className="text-gray-500">Skipped wizard</div>}
                    </td>
                    <td className="px-4 py-3">
                      {row.health_flags.length === 0 ? (
                        <span className="text-xs text-gray-500">OK</span>
                      ) : (
                        <div className="space-y-1">
                          {row.health_flags.map((flag) => (
                            <span
                              key={flag}
                              title={FLAG_LABELS[flag] ?? flag}
                              className="block rounded bg-red-950/40 px-2 py-0.5 text-[10px] text-red-300"
                            >
                              {flag.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <p className="mt-4 text-xs text-gray-500">
        Tenant owners configure integrations in their dashboard at{' '}
        <Link href="/dashboard/integrations" className="text-amber-400 hover:underline">
          /dashboard/integrations
        </Link>
        . Use Tenants → Impersonate to open a tenant&apos;s integration settings.
      </p>
    </div>
  )
}
