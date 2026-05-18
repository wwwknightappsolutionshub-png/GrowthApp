'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mail, Megaphone, Plus, Pencil, Trash2 } from 'lucide-react'
import { adminApi, type CommTemplate, type BroadcastItem } from '@/lib/api-client'

type Tab = 'templates' | 'broadcasts'

const EMPTY_TMPL = { name: '', channel: 'email', subject: '', body: '', is_active: true }
const EMPTY_BCAST = { name: '', channel: 'email', body: '', target_filter: {}, scheduled_at: '' }
const CHANNELS = ['email', 'sms', 'whatsapp']

export default function CommunicationsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('templates')
  const [modal, setModal] = useState<null | 'create' | CommTemplate>(null)
  const [bcastModal, setBcastModal] = useState(false)
  const [form, setForm] = useState(EMPTY_TMPL)
  const [bcastForm, setBcastForm] = useState(EMPTY_BCAST)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: templates = [] } = useQuery({ queryKey: ['admin', 'comms', 'templates'], queryFn: () => adminApi.listCommTemplates().then(r => r.data) })
  const { data: broadcasts = [] } = useQuery({ queryKey: ['admin', 'comms', 'broadcasts'], queryFn: () => adminApi.listBroadcasts().then(r => r.data) })

  const saveMut = useMutation({
    mutationFn: () => modal === 'create' ? adminApi.createCommTemplate(form) : adminApi.updateCommTemplate((modal as CommTemplate).id, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'comms'] }); setModal(null); showToast('Template saved') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteCommTemplate(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'comms'] }); setDeleteId(null) },
  })
  const bcastMut = useMutation({
    mutationFn: () => adminApi.createBroadcast({ ...bcastForm, target_filter: {} }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'comms'] }); setBcastModal(false); showToast('Broadcast scheduled') },
  })

  const CHANNEL_COLORS: Record<string, string> = { email: 'bg-blue-900/30 text-blue-400', sms: 'bg-green-900/30 text-green-400', whatsapp: 'bg-emerald-900/30 text-emerald-400' }

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Mail className="h-6 w-6 text-amber-400" /> Communication Hub</h1>
        <p className="text-sm text-gray-400 mt-1">Manage email/SMS templates and broadcast messages</p>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <div className="flex gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1 w-fit">
          {(['templates', 'broadcasts'] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
              {t}
            </button>
          ))}
        </div>
        {tab === 'templates'
          ? <button onClick={() => { setForm(EMPTY_TMPL); setModal('create') }} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400"><Plus className="h-4 w-4" /> Add Template</button>
          : <button onClick={() => { setBcastForm(EMPTY_BCAST); setBcastModal(true) }} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400"><Megaphone className="h-4 w-4" /> New Broadcast</button>
        }
      </div>

      {tab === 'templates' && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Name', 'Channel', 'Subject', 'Status', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(templates as CommTemplate[]).length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No templates yet</td></tr>}
              {(templates as CommTemplate[]).map(t => (
                <tr key={t.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CHANNEL_COLORS[t.channel] ?? 'bg-gray-700 text-gray-400'}`}>{t.channel}</span></td>
                  <td className="px-4 py-3 text-gray-400">{t.subject ?? '—'}</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs ${t.is_active ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-500'}`}>{t.is_active ? 'Active' : 'Inactive'}</span></td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => { setForm({ name: t.name, channel: t.channel, subject: t.subject ?? '', body: t.body, is_active: t.is_active }); setModal(t) }} className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white"><Pencil className="h-4 w-4" /></button>
                      <button onClick={() => setDeleteId(t.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'broadcasts' && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Name', 'Channel', 'Status', 'Recipients', 'Created'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(broadcasts as BroadcastItem[]).length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No broadcasts yet</td></tr>}
              {(broadcasts as BroadcastItem[]).map(b => (
                <tr key={b.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{b.name}</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CHANNEL_COLORS[b.channel] ?? 'bg-gray-700 text-gray-400'}`}>{b.channel}</span></td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs ${b.status === 'sent' ? 'bg-green-900/30 text-green-400' : b.status === 'pending' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-gray-700 text-gray-400'}`}>{b.status}</span></td>
                  <td className="px-4 py-3 text-gray-400">{b.recipient_count}</td>
                  <td className="px-4 py-3 text-gray-400">{new Date(b.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Template modal */}
      {modal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-lg rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">{modal === 'create' ? 'Add Template' : 'Edit Template'}</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">Name</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Channel</label>
                <select value={form.channel} onChange={e => setForm(f => ({ ...f, channel: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
                  {CHANNELS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              {form.channel === 'email' && <div><label className="mb-1 block text-xs text-gray-400">Subject</label><input value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>}
              <div><label className="mb-1 block text-xs text-gray-400">Body</label><textarea rows={5} value={form.body} onChange={e => setForm(f => ({ ...f, body: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500 resize-none" /></div>
              <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} /><span className="text-sm text-gray-300">Active</span></label>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setModal(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{saveMut.isPending ? 'Saving…' : 'Save'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Broadcast modal */}
      {bcastModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">New Broadcast</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">Name</label><input value={bcastForm.name} onChange={e => setBcastForm(f => ({ ...f, name: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Channel</label><select value={bcastForm.channel} onChange={e => setBcastForm(f => ({ ...f, channel: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">{CHANNELS.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
              <div><label className="mb-1 block text-xs text-gray-400">Message Body</label><textarea rows={4} value={bcastForm.body} onChange={e => setBcastForm(f => ({ ...f, body: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500 resize-none" /></div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setBcastModal(false)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => bcastMut.mutate()} disabled={bcastMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{bcastMut.isPending ? 'Sending…' : 'Schedule'}</button>
            </div>
          </div>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Template</h2>
            <p className="mb-5 text-sm text-gray-400">This action cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteId(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => deleteMut.mutate(deleteId)} disabled={deleteMut.isPending} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50">{deleteMut.isPending ? 'Deleting…' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
