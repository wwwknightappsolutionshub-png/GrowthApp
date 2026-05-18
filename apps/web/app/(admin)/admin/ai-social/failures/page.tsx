'use client'

import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface PublishError {
  id: string
  tenant_name: string
  draft_id: string
  platform: string
  scheduled_time: string | null
}

interface RevisionRequest {
  draft_id: string
  tenant_name: string
  text_content: string
  ai_notes: string
  created_at: string | null
}

export default function AiSocialFailuresPage() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['admin', 'social', 'failures'],
    queryFn: () => adminApi.socialFailures().then((r) => r.data),
  })

  const errors: PublishError[] = data?.publish_errors ?? []
  const revisions: RevisionRequest[] = data?.revision_requests ?? []

  return (
    <div className="text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-red-400" /> Failure Logs
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Drafts that failed to publish + revision requests from tenants.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="space-y-6">
        <section>
          <h2 className="text-sm font-semibold uppercase text-gray-400 mb-2">
            Publish errors ({errors.length})
          </h2>
          <div className="rounded-xl border border-red-900/40 bg-gray-900 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-800/60 text-gray-400 text-xs uppercase tracking-wider">
                <tr>
                  {['Tenant', 'Platform', 'Draft', 'Scheduled time'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {isLoading && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                      Loading…
                    </td>
                  </tr>
                )}
                {!isLoading && errors.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                      No publish errors
                    </td>
                  </tr>
                )}
                {errors.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-800/40">
                    <td className="px-4 py-2 font-medium">{e.tenant_name}</td>
                    <td className="px-4 py-2 text-amber-300">{e.platform}</td>
                    <td className="px-4 py-2 text-xs text-gray-400 font-mono">
                      {e.draft_id.slice(0, 8)}
                    </td>
                    <td className="px-4 py-2 text-gray-400">
                      {e.scheduled_time ? new Date(e.scheduled_time).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold uppercase text-gray-400 mb-2">
            Revision requests ({revisions.length})
          </h2>
          <div className="rounded-xl border border-amber-900/40 bg-gray-900 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-800/60 text-gray-400 text-xs uppercase tracking-wider">
                <tr>
                  {['Tenant', 'Content', 'AI notes', 'Created'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {isLoading && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                      Loading…
                    </td>
                  </tr>
                )}
                {!isLoading && revisions.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                      No revision requests
                    </td>
                  </tr>
                )}
                {revisions.map((r) => (
                  <tr key={r.draft_id} className="hover:bg-gray-800/40 align-top">
                    <td className="px-4 py-2 font-medium">{r.tenant_name}</td>
                    <td className="px-4 py-2 text-gray-300 max-w-md">{r.text_content}</td>
                    <td className="px-4 py-2 text-gray-500 text-xs max-w-xs">{r.ai_notes}</td>
                    <td className="px-4 py-2 text-gray-400">
                      {r.created_at ? new Date(r.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
