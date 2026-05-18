'use client'

import { useQuery } from '@tanstack/react-query'
import { CalendarClock, RefreshCw } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface ScheduleItem {
  id: string
  tenant_name: string
  draft_id: string
  platform: string
  scheduled_time: string | null
  posted_status: string | null
}

export default function AiSocialSchedulerPage() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['admin', 'social', 'scheduler'],
    queryFn: () => adminApi.socialScheduler().then((r) => r.data),
  })

  const counts: Record<string, number> = data?.counts_by_status ?? {}
  const items: ScheduleItem[] = data?.items ?? []
  const overdue = data?.overdue ?? 0

  return (
    <div className="text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CalendarClock className="h-6 w-6 text-amber-400" /> Scheduler Status
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time view of the AI Social posting queue.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          ['Scheduled', counts['SCHEDULED'] ?? 0, 'text-amber-300'],
          ['Published', counts['PUBLISHED'] ?? 0, 'text-green-400'],
          ['Errored', counts['ERROR'] ?? 0, 'text-red-400'],
          ['Overdue (past due, not posted)', overdue, 'text-orange-400'],
        ].map(([label, val, color]) => (
          <div
            key={label as string}
            className="rounded-xl bg-gray-900 border border-gray-800 p-4"
          >
            <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
            <div className={`text-2xl font-bold mt-1 ${color as string}`}>{val as number}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800 text-sm font-semibold">
          Upcoming queue ({items.length})
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-800/60 text-gray-400 text-xs uppercase tracking-wider">
            <tr>
              {['Tenant', 'Platform', 'Scheduled', 'Status', 'Draft'].map((h) => (
                <th key={h} className="px-4 py-3 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                  No scheduled items
                </td>
              </tr>
            )}
            {items.map((it) => (
              <tr key={it.id} className="hover:bg-gray-800/40">
                <td className="px-4 py-2 font-medium">{it.tenant_name}</td>
                <td className="px-4 py-2 text-amber-300">{it.platform}</td>
                <td className="px-4 py-2 text-gray-400">
                  {it.scheduled_time ? new Date(it.scheduled_time).toLocaleString() : '—'}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      it.posted_status === 'PUBLISHED'
                        ? 'bg-green-900/40 text-green-300'
                        : it.posted_status === 'ERROR'
                          ? 'bg-red-900/40 text-red-300'
                          : 'bg-amber-900/40 text-amber-300'
                    }`}
                  >
                    {it.posted_status}
                  </span>
                </td>
                <td className="px-4 py-2 text-xs text-gray-400 font-mono">
                  {it.draft_id.slice(0, 8)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
