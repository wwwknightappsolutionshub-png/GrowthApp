'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, Search, ChevronDown, ChevronRight } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface Result {
  id: string; task_id: string; url: string; ai_score: number; status: string;
  extracted_json: Record<string, unknown> | null; created_at: string
}

const SCORE_COLOR = (s: number) => s >= 80 ? 'text-green-400 bg-green-900/30' : s >= 50 ? 'text-amber-400 bg-amber-900/30' : 'text-red-400 bg-red-900/30'

export default function ScraperResultsPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data: results = [], isLoading } = useQuery({
    queryKey: ['admin', 'scraper-results'],
    queryFn: () => adminApi.listScraperResults({ limit: 200 }).then(r => r.data as Result[]),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteScraperResult(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'scraper-results'] }); setDeleteId(null) },
  })

  const filtered = results.filter(r =>
    !search || r.url.toLowerCase().includes(search.toLowerCase()) || r.status.includes(search)
  )

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Scraper Results</h1>
          <p className="text-sm text-gray-400 mt-1">View extracted lead data from completed scraper tasks</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search URL or status…"
            className="rounded-lg border border-gray-700 bg-gray-800 pl-9 pr-3 py-2 text-sm text-white outline-none focus:border-amber-500 w-56" />
        </div>
      </div>

      {isLoading ? <div className="text-gray-400">Loading...</div> : (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['', 'URL', 'AI Score', 'Status', 'Created', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No results yet</td></tr>}
              {filtered.map(r => (
                <>
                  <tr key={r.id} className="hover:bg-gray-800/50">
                    <td className="px-4 py-3 w-6">
                      {r.extracted_json && (
                        <button onClick={() => setExpanded(expanded === r.id ? null : r.id)} className="text-gray-400 hover:text-white">
                          {expanded === r.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-300 truncate max-w-xs">
                      <a href={r.url} target="_blank" rel="noopener noreferrer" className="hover:text-amber-400 truncate block max-w-xs">{r.url}</a>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${SCORE_COLOR(r.ai_score)}`}>{r.ai_score}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${r.status === 'processed' ? 'bg-green-900/30 text-green-400' : r.status === 'failed' ? 'bg-red-900/30 text-red-400' : 'bg-gray-700 text-gray-400'}`}>{r.status}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{new Date(r.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => setDeleteId(r.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                  {expanded === r.id && r.extracted_json && (
                    <tr key={`${r.id}-exp`} className="bg-gray-900/80">
                      <td colSpan={6} className="px-6 pb-4">
                        <pre className="text-xs text-gray-300 bg-gray-800 rounded-lg p-3 overflow-x-auto max-h-48">
                          {JSON.stringify(r.extracted_json, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Result</h2>
            <p className="mb-5 text-sm text-gray-400">This action cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteId(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => deleteMut.mutate(deleteId)} disabled={deleteMut.isPending} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50">
                {deleteMut.isPending ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
