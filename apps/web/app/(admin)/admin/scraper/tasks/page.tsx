'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Play, Clock } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface Task { id: string; name: string; source_id: string; aggression_level: string; status: string; cron_expression: string | null; max_pages: number; is_active: boolean; created_at: string }

const EMPTY = { name: '', source_id: '', aggression_level: 'low', cron_expression: '', max_pages: 5, is_active: true }

const STATUS_COLORS: Record<string, string> = {
  idle: 'text-gray-400 bg-gray-800',
  running: 'text-blue-400 bg-blue-900/30',
  completed: 'text-green-400 bg-green-900/30',
  failed: 'text-red-400 bg-red-900/30',
}

export default function ScraperTasksPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState<null | 'create' | Task>(null)
  const [form, setForm] = useState(EMPTY)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set())

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['admin', 'scraper-tasks'],
    queryFn: () => adminApi.listScraperTasks().then(r => r.data as Task[]),
  })

  function openCreate() { setForm(EMPTY); setModal('create') }
  function openEdit(t: Task) {
    setForm({ name: t.name, source_id: t.source_id, aggression_level: t.aggression_level, cron_expression: t.cron_expression ?? '', max_pages: t.max_pages, is_active: t.is_active })
    setModal(t)
  }

  const saveMut = useMutation({
    mutationFn: () => modal === 'create'
      ? adminApi.createScraperTask(form)
      : adminApi.updateScraperTask((modal as Task).id, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'scraper-tasks'] }); setModal(null) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteScraperTask(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'scraper-tasks'] }); setDeleteId(null) },
  })

  async function runTask(id: string) {
    setRunningIds(s => new Set(s).add(id))
    try { await adminApi.runScraperTask(id) } finally { setRunningIds(s => { const n = new Set(s); n.delete(id); return n }) }
    qc.invalidateQueries({ queryKey: ['admin', 'scraper-tasks'] })
  }

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Scraper Tasks</h1>
          <p className="text-sm text-gray-400 mt-1">Configure and schedule crawl tasks with aggression levels</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
          <Plus className="h-4 w-4" /> Add Task
        </button>
      </div>

      {isLoading ? <div className="text-gray-400">Loading...</div> : (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Name', 'Aggression', 'Schedule', 'Max Pages', 'Status', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {tasks.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No tasks yet</td></tr>}
              {tasks.map(t => (
                <tr key={t.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${t.aggression_level === 'high' ? 'bg-red-900/40 text-red-400' : t.aggression_level === 'medium' ? 'bg-yellow-900/40 text-yellow-400' : 'bg-green-900/40 text-green-400'}`}>
                      {t.aggression_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {t.cron_expression ? <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{t.cron_expression}</span> : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{t.max_pages}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_COLORS[t.status] ?? 'text-gray-400 bg-gray-800'}`}>{t.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => runTask(t.id)} disabled={runningIds.has(t.id)} title="Run now" className="rounded p-1.5 text-gray-400 hover:bg-green-900 hover:text-green-400 disabled:opacity-40">
                        <Play className="h-4 w-4" />
                      </button>
                      <button onClick={() => openEdit(t)} className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button onClick={() => setDeleteId(t.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400">
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

      {modal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">{modal === 'create' ? 'Add Task' : 'Edit Task'}</h2>
            <div className="space-y-3">
              {([['name', 'Task Name'], ['source_id', 'Source ID'], ['cron_expression', 'Cron Expression (optional)']] as const).map(([key, label]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs text-gray-400">{label}</label>
                  <input value={String(form[key as keyof typeof form])} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" placeholder={label} />
                </div>
              ))}
              <div>
                <label className="mb-1 block text-xs text-gray-400">Aggression Level</label>
                <select value={form.aggression_level} onChange={e => setForm(f => ({ ...f, aggression_level: e.target.value }))}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
                  {['low', 'medium', 'high'].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Max Pages</label>
                <input type="number" min={1} max={100} value={form.max_pages} onChange={e => setForm(f => ({ ...f, max_pages: Number(e.target.value) }))}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
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

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Task</h2>
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
