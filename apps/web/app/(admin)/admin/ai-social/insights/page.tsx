'use client'

import { useQuery } from '@tanstack/react-query'
import { BarChart3, Users } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface TenantRow {
  id: string
  name: string
  drafts: number
  approvals_sent: number
  scheduled: number
  published: number
  errors: number
}

export default function AiSocialInsightsPage() {
  const overview = useQuery({
    queryKey: ['admin', 'social', 'tenant-overview'],
    queryFn: () => adminApi.socialTenantOverview().then((r) => r.data),
  })
  const insights = useQuery({
    queryKey: ['admin', 'social', 'insights'],
    queryFn: () => adminApi.socialInsights().then((r) => r.data),
  })

  const o = overview.data
  const tenants: TenantRow[] = insights.data?.tenants ?? []

  return (
    <div className="text-white">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users className="h-6 w-6 text-amber-400" /> Tenant Insights
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          AI Social usage by tenant — drafts, approvals, scheduled, published, errors.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          ['Pending approvals', o?.pending_approvals ?? '—'],
          ['Scheduled posts', o?.scheduled_posts ?? '—'],
          ['Published posts', o?.published_posts ?? '—'],
          [
            'Total drafts',
            o
              ? Object.values<number>(o.drafts_by_status || {}).reduce((a, b) => a + b, 0)
              : '—',
          ],
        ].map(([label, val]) => (
          <div key={label as string} className="rounded-xl bg-gray-900 border border-gray-800 p-4">
            <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
            <div className="text-2xl font-bold mt-1">{val as number}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
          <BarChart3 className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-semibold">Per-tenant breakdown</span>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-800/60 text-gray-400 text-xs uppercase tracking-wider">
            <tr>
              {['Tenant', 'Drafts', 'Approvals sent', 'Scheduled', 'Published', 'Errors'].map(
                (h) => (
                  <th key={h} className="px-4 py-3 text-left">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {insights.isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {!insights.isLoading && tenants.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No tenant activity yet
                </td>
              </tr>
            )}
            {tenants.map((t) => (
              <tr key={t.id} className="hover:bg-gray-800/40">
                <td className="px-4 py-2 font-medium">{t.name}</td>
                <td className="px-4 py-2">{t.drafts}</td>
                <td className="px-4 py-2">{t.approvals_sent}</td>
                <td className="px-4 py-2">{t.scheduled}</td>
                <td className="px-4 py-2 text-green-400">{t.published}</td>
                <td className="px-4 py-2 text-red-400">{t.errors}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
