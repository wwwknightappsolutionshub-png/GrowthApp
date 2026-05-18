'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { HeadphonesIcon, Plus, CheckCircle, Trash2, MessageSquare, ChevronDown, ChevronRight } from 'lucide-react'
import { adminApi, type SupportTicket, type TicketReply } from '@/lib/api-client'

const PRIORITY_COLORS: Record<string, string> = { urgent: 'bg-red-900/30 text-red-400', high: 'bg-orange-900/30 text-orange-400', normal: 'bg-blue-900/30 text-blue-400', low: 'bg-gray-700 text-gray-400' }
const STATUS_COLORS: Record<string, string> = { open: 'bg-green-900/30 text-green-400', pending: 'bg-yellow-900/30 text-yellow-400', resolved: 'bg-gray-700 text-gray-400' }

export default function SupportPage() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [replyText, setReplyText] = useState('')
  const [createModal, setCreateModal] = useState(false)
  const [createForm, setCreateForm] = useState({ subject: '', body: '', priority: 'normal' })
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: tickets = [], isLoading } = useQuery({
    queryKey: ['admin', 'support', 'tickets', statusFilter],
    queryFn: () => adminApi.listTickets({ status: statusFilter || undefined }).then(r => r.data),
  })
  const { data: ticketDetail } = useQuery({
    queryKey: ['admin', 'support', 'ticket', expandedId],
    queryFn: () => expandedId ? adminApi.getTicket(expandedId).then(r => r.data) : null,
    enabled: !!expandedId,
  })

  const createMut = useMutation({
    mutationFn: () => adminApi.createTicket(createForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'support'] }); setCreateModal(false); showToast('Ticket created') },
  })
  const resolveMut = useMutation({
    mutationFn: (id: string) => adminApi.resolveTicket(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'support'] }); showToast('Ticket resolved') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteTicket(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'support'] }); setDeleteId(null) },
  })
  const replyMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) => adminApi.replyTicket(id, { body }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'support', 'ticket', expandedId] }); setReplyText(''); showToast('Reply sent') },
  })

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><HeadphonesIcon className="h-6 w-6 text-amber-400" /> Helpdesk & Support</h1>
          <p className="text-sm text-gray-400 mt-1">Manage support tickets, replies and issue resolution</p>
        </div>
        <div className="flex gap-3">
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
            <option value="">All Status</option>
            {['open', 'pending', 'resolved'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
            <Plus className="h-4 w-4" /> New Ticket
          </button>
        </div>
      </div>

      {isLoading ? <div className="text-gray-400">Loading...</div> : (
        <div className="space-y-2">
          {(tickets as SupportTicket[]).length === 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-900 py-12 text-center text-gray-500">No tickets found</div>
          )}
          {(tickets as SupportTicket[]).map(t => (
            <div key={t.id} className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
              <div className="flex items-center gap-3 px-5 py-4 hover:bg-gray-800/50 cursor-pointer" onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}>
                <button className="text-gray-400">{expandedId === t.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}</button>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{t.subject}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{new Date(t.created_at).toLocaleString()}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${PRIORITY_COLORS[t.priority] ?? 'bg-gray-700 text-gray-400'}`}>{t.priority}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_COLORS[t.status] ?? 'bg-gray-700 text-gray-400'}`}>{t.status}</span>
                <div className="flex gap-1 ml-2" onClick={e => e.stopPropagation()}>
                  {t.status !== 'resolved' && (
                    <button onClick={() => resolveMut.mutate(t.id)} title="Mark resolved" className="rounded p-1.5 text-gray-400 hover:bg-green-900 hover:text-green-400"><CheckCircle className="h-4 w-4" /></button>
                  )}
                  <button onClick={() => setDeleteId(t.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>

              {expandedId === t.id && ticketDetail && (
                <div className="border-t border-gray-800 px-5 py-4">
                  <p className="text-sm text-gray-300 mb-4 whitespace-pre-wrap">{(ticketDetail as SupportTicket & { body?: string }).body ?? ''}</p>
                  <div className="space-y-3 mb-4">
                    {((ticketDetail as SupportTicket & { replies?: TicketReply[] }).replies ?? []).map(r => (
                      <div key={r.id} className={`rounded-lg p-3 text-sm ${r.is_internal ? 'bg-yellow-900/20 border border-yellow-800/40' : 'bg-gray-800'}`}>
                        {r.is_internal && <span className="text-xs text-yellow-400 font-semibold block mb-1">Internal Note</span>}
                        <p className="text-gray-300">{r.body}</p>
                        <p className="text-xs text-gray-500 mt-1">{new Date(r.created_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <textarea rows={2} value={replyText} onChange={e => setReplyText(e.target.value)} placeholder="Write a reply…"
                      className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500 resize-none" />
                    <button onClick={() => replyMut.mutate({ id: t.id, body: replyText })} disabled={!replyText.trim() || replyMut.isPending}
                      className="flex items-center gap-1 rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">
                      <MessageSquare className="h-4 w-4" /> Reply
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {createModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">Create Ticket</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">Subject</label><input value={createForm.subject} onChange={e => setCreateForm(f => ({ ...f, subject: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Priority</label>
                <select value={createForm.priority} onChange={e => setCreateForm(f => ({ ...f, priority: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
                  {['low', 'normal', 'high', 'urgent'].map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div><label className="mb-1 block text-xs text-gray-400">Description</label><textarea rows={4} value={createForm.body} onChange={e => setCreateForm(f => ({ ...f, body: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500 resize-none" /></div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setCreateModal(false)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{createMut.isPending ? 'Creating…' : 'Create'}</button>
            </div>
          </div>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Ticket</h2>
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
