'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Save, Plus, Trash2, Eye, EyeOff } from 'lucide-react'
import { adminApi, type SystemSetting } from '@/lib/api-client'

export default function SettingsPage() {
  const qc = useQueryClient()
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [newForm, setNewForm] = useState({ key: '', value: '', description: '', is_secret: false })
  const [showNew, setShowNew] = useState(false)
  const [deleteKey, setDeleteKey] = useState<string | null>(null)
  const [revealed, setRevealed] = useState<Set<string>>(new Set())
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: settings = [], isLoading } = useQuery({ queryKey: ['admin', 'settings'], queryFn: () => adminApi.listSettings().then(r => r.data) })

  const updateMut = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => adminApi.updateSetting(key, value),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'settings'] }); setEditingKey(null); showToast('Setting saved') },
  })
  const createMut = useMutation({
    mutationFn: () => adminApi.bulkUpsertSettings([{ key: newForm.key, value: newForm.value, description: newForm.description }]),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'settings'] }); setShowNew(false); setNewForm({ key: '', value: '', description: '', is_secret: false }); showToast('Setting created') },
  })
  const deleteMut = useMutation({
    mutationFn: (key: string) => adminApi.deleteSetting(key),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'settings'] }); setDeleteKey(null); showToast('Setting deleted') },
  })

  function startEdit(s: SystemSetting) { setEditingKey(s.key); setEditValue(s.is_secret ? '' : JSON.stringify(s.value ?? '')) }

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Settings className="h-6 w-6 text-amber-400" /> System Settings</h1>
          <p className="text-sm text-gray-400 mt-1">Global configuration keys and values for the CustomerFlow platform</p>
        </div>
        <button onClick={() => setShowNew(true)} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
          <Plus className="h-4 w-4" /> Add Setting
        </button>
      </div>

      {isLoading ? <div className="text-gray-400">Loading...</div> : (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Key', 'Value', 'Description', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(settings as SystemSetting[]).length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No settings configured</td></tr>}
              {(settings as SystemSetting[]).map(s => (
                <tr key={s.key} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono text-amber-300 text-xs">{s.key}</td>
                  <td className="px-4 py-3 max-w-xs">
                    {editingKey === s.key ? (
                      <div className="flex gap-2">
                        <input value={editValue} onChange={e => setEditValue(e.target.value)} className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-white outline-none focus:border-amber-500" />
                        <button onClick={() => updateMut.mutate({ key: s.key, value: editValue })} className="rounded bg-amber-500 px-2 py-1 text-xs text-black font-semibold hover:bg-amber-400">Save</button>
                        <button onClick={() => setEditingKey(null)} className="rounded border border-gray-700 px-2 py-1 text-xs text-gray-400 hover:bg-gray-700">×</button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        {s.is_secret ? (
                          <>
                            <span className="text-xs text-gray-500">{revealed.has(s.key) ? JSON.stringify(s.value) : '••••••••'}</span>
                            <button onClick={() => setRevealed(r => { const n = new Set(r); n.has(s.key) ? n.delete(s.key) : n.add(s.key); return n })} className="text-gray-500 hover:text-gray-300">
                              {revealed.has(s.key) ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                            </button>
                          </>
                        ) : (
                          <span className="text-xs text-gray-300 truncate max-w-[16rem]">{JSON.stringify(s.value)}</span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{s.description || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => startEdit(s)} className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white"><Save className="h-4 w-4" /></button>
                      <button onClick={() => setDeleteKey(s.key)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showNew && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">Add Setting</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">Key</label><input value={newForm.key} onChange={e => setNewForm(f => ({ ...f, key: e.target.value }))} placeholder="e.g. STRIPE_WEBHOOK_SECRET" className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white font-mono outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Value</label><input value={newForm.value} onChange={e => setNewForm(f => ({ ...f, value: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Description</label><input value={newForm.description} onChange={e => setNewForm(f => ({ ...f, description: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setShowNew(false)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending || !newForm.key} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{createMut.isPending ? 'Saving…' : 'Save'}</button>
            </div>
          </div>
        </div>
      )}

      {deleteKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Setting</h2>
            <p className="mb-1 text-sm text-gray-300">Key: <span className="font-mono text-amber-300">{deleteKey}</span></p>
            <p className="mb-5 text-sm text-gray-400">This action cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteKey(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => deleteMut.mutate(deleteKey)} disabled={deleteMut.isPending} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50">{deleteMut.isPending ? 'Deleting…' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
