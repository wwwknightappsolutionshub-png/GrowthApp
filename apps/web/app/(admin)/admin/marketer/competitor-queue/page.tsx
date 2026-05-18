'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, RefreshCw, Search } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface CompetitorItem {
  id: string
  tenant_name: string
  competitor_name: string | null
  website: string | null
  strengths: string[]
  weaknesses: string[]
  pricing_samples: string[]
  positioning_gaps: string[]
  fetch_error: string | null
}

export default function CompetitorQueueMonitorPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['admin', 'marketer', 'competitor-queue'],
    queryFn: () => adminApi.marketerCompetitorQueue().then((r) => r.data),
  })

  const items: CompetitorItem[] = data?.items ?? []
  const total = data?.total ?? 0
  const fetchErrors = data?.fetch_errors ?? 0
  const term = search.trim().toLowerCase()
  const filtered = term
    ? items.filter(
        (i) =>
          (i.competitor_name || '').toLowerCase().includes(term) ||
          (i.website || '').toLowerCase().includes(term) ||
          (i.tenant_name || '').toLowerCase().includes(term),
      )
    : items

  return (
    <div className="text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Search className="h-6 w-6 text-amber-400" /> Competitor Intelligence Queue Monitor
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Every competitor scan submitted by tenants, with extracted strengths, weaknesses,
            pricing, and positioning gaps.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        {[
          ['Total scans', total, 'text-amber-300'],
          ['Showing', filtered.length, 'text-gray-200'],
          ['Fetch errors', fetchErrors, 'text-red-400'],
        ].map(([label, val, color]) => (
          <div key={label as string} className="rounded-xl bg-gray-900 border border-gray-800 p-4">
            <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
            <div className={`text-2xl font-bold mt-1 ${color as string}`}>{val as number}</div>
          </div>
        ))}
      </div>

      <div className="mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search competitor, website, or tenant…"
          className="w-full max-w-md rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-12 text-center text-gray-500">
          No competitor scans found
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((c) => (
            <div
              key={c.id}
              className="rounded-xl border border-gray-800 bg-gray-900 p-5 grid grid-cols-1 md:grid-cols-4 gap-4"
            >
              <div className="md:col-span-1">
                <div className="text-xs uppercase tracking-wider text-gray-500">Tenant</div>
                <div className="font-medium">{c.tenant_name}</div>
                <div className="mt-3 text-xs uppercase tracking-wider text-gray-500">
                  Competitor
                </div>
                <div className="font-semibold text-amber-300">{c.competitor_name || '—'}</div>
                {c.website && (
                  <a
                    href={c.website.startsWith('http') ? c.website : `https://${c.website}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                  >
                    {c.website} <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {c.fetch_error && (
                  <div className="mt-2 text-xs rounded bg-red-900/30 border border-red-900 px-2 py-1 text-red-300">
                    Fetch error: {c.fetch_error}
                  </div>
                )}
              </div>

              <Column title="Strengths" items={c.strengths} color="text-green-400" />
              <Column title="Weaknesses" items={c.weaknesses} color="text-red-400" />
              <div className="space-y-3">
                <Column title="Pricing samples" items={c.pricing_samples} color="text-amber-300" />
                <Column
                  title="Positioning gaps"
                  items={c.positioning_gaps}
                  color="text-blue-300"
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Column({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">{title}</div>
      {items.length === 0 ? (
        <div className="text-xs text-gray-600">—</div>
      ) : (
        <ul className={`text-xs space-y-0.5 ${color}`}>
          {items.map((s, i) => (
            <li key={i}>• {s}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
