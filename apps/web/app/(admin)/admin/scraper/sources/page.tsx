'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Globe, ToggleLeft, ToggleRight } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface Source { id: string; name: string; url: string; scraping_type: string; is_active: boolean; created_at: string }

const EMPTY: Omit<Source, 'id' | 'created_at'> = { name: '', url: '', scraping_type: 'html', is_active: true }

export default function ScraperSourcesPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState<null | 'create' | Source>(null)
  const [form, setForm] = useState(EMPTY)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['admin', 'scraper-sources'],
    queryFn: () => adminApi.listScraperSources().then(r => r.data as Source[]),
  })

  function openCreate() { setForm(EMPTY); setModal('create') }
  function openEdit(s: Source) { setForm({ name: s.name, url: s.url, scraping_type: s.scraping_type, is_active: s.is_active }); setModal(s) }

  const saveMut = useMutation({
    mutationFn: () => modal === 'create'
      ? adminApi.createScraperSource(form)
      : adminApi.updateScraperSource((modal as Source).id, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'scraper-sources'] }); setModal(null) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteScraperSource(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'scraper-sources'] }); setDeleteId(null) },
  })

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Scraper Sources</h1>
          <p className="text-sm text-gray-400 mt-1">Manage websites and data sources for the AI scraper engine</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
          <Plus className="h-4 w-4" /> Add Source
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>
                {['Name', 'URL', 'Type', 'Status', 'Created', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {sources.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No sources yet</td></tr>
              )}
              {sources.map((s) => (
                <tr key={s.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3 text-gray-400 truncate max-w-xs">
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-amber-400">
                      <Globe className="h-3 w-3" /> {s.url}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs">{s.scraping_type}</span>
                  </td>
                  <td className="px-4 py-3">
                    {s.is_active
                      ? <span className="flex items-center gap-1 text-green-400"><ToggleRight className="h-4 w-4" /> Active</span>
                      : <span className="flex items-center gap-1 text-gray-500"><ToggleLeft className="h-4 w-4" /> Inactive</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{new Date(s.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(s)} className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button onClick={() => setDeleteId(s.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Modal */}
      {modal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">{modal === 'create' ? 'Add Source' : 'Edit Source'}</h2>
            <div className="space-y-3">
              {([['name', 'Name', 'text'], ['url', 'URL', 'url'], ['scraping_type', 'Scraping Type', 'text']] as const).map(([key, label, type]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs text-gray-400">{label}</label>
                  <input
                    type={type}
                    value={String(form[key as keyof typeof form])}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
                    placeholder={label}
                  />
                </div>
              ))}
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} className="rounded" />
                <span className="text-sm text-gray-300">Active</span>
              </label>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setModal(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">
                {saveMut.isPending ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold text-white">Delete Source</h2>
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
