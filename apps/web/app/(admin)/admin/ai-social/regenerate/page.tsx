'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface TenantOption {
  id: string
  name: string
  draft_count: number
}

export default function AiSocialRegeneratePage() {
  const [tenantId, setTenantId] = useState('')
  const [count, setCount] = useState(3)
  const [topics, setTopics] = useState('')
  const [result, setResult] = useState<string[] | null>(null)
  const [toast, setToast] = useState('')

  const tenants = useQuery({
    queryKey: ['admin', 'social', 'tenants-list'],
    queryFn: () => adminApi.socialTenantsList().then((r) => r.data),
  })
  const opts: TenantOption[] = tenants.data ?? []

  const generateMut = useMutation({
    mutationFn: (body: { tenant_id: string; count: number; topic_hints?: string[] }) =>
      adminApi.socialForceGenerate(body),
    onSuccess: (res) => {
      const ids: string[] = res.data?.draft_ids ?? []
      setResult(ids)
      setToast(`Generated ${ids.length} draft(s)`)
      setTimeout(() => setToast(''), 3000)
    },
  })

  function run() {
    if (!tenantId) {
      setToast('Pick a tenant first')
      setTimeout(() => setToast(''), 2500)
      return
    }
    const hints = topics
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    generateMut.mutate({
      tenant_id: tenantId,
      count,
      topic_hints: hints.length ? hints : undefined,
    })
  }

  return (
    <div className="text-white">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium shadow-lg">
          {toast}
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-amber-400" /> Manual Regeneration
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Force-generate AI Social drafts on behalf of a tenant. Useful for unblocking stuck
          accounts or running a one-off campaign.
        </p>
      </div>

      <div className="max-w-2xl rounded-xl border border-gray-800 bg-gray-900 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Tenant</label>
          <select
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
          >
            <option value="">— Choose a tenant —</option>
            {opts.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name} ({o.draft_count} drafts)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Number of drafts
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={count}
            onChange={(e) => setCount(parseInt(e.target.value || '1', 10))}
            className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Topic hints (one per line, optional)
          </label>
          <textarea
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            rows={4}
            placeholder={'Summer promo\nNew service launch\nCustomer testimonial'}
            className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm font-mono"
          />
        </div>

        <button
          onClick={run}
          disabled={generateMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-amber-500 px-5 py-3 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-60"
        >
          <Sparkles className="h-4 w-4" />
          {generateMut.isPending ? 'Generating…' : 'Force-generate drafts'}
        </button>

        {result && result.length > 0 && (
          <div className="rounded-lg bg-gray-800/60 border border-gray-700 p-4">
            <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">
              Generated draft IDs
            </div>
            <ul className="text-xs font-mono text-amber-300 space-y-0.5">
              {result.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
