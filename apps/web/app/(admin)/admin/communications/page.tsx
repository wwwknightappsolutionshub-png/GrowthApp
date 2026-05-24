'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mail, Megaphone, Plus, Pencil, Trash2, Send } from 'lucide-react'
import { adminApi, type CommTemplate, type BroadcastItem } from '@/lib/api-client'

type Tab = 'templates' | 'broadcasts'

const EMPTY_TMPL = { name: '', channel: 'email', subject: '', body: '', is_active: true }
const EMPTY_BCAST = {
  name: '',
  channel: 'push',
  body: '',
  target_filter: { audience: 'tenant_owners', link: '/dashboard/notifications' },
  scheduled_at: '',
}
const TMPL_CHANNELS = ['email', 'sms', 'whatsapp']
const BROADCAST_CHANNELS = [
  { id: 'push', label: 'In-app + push alert' },
  { id: 'in_app', label: 'In-app only' },
  { id: 'push_only', label: 'Push only (no bell)' },
  { id: 'email', label: 'Email' },
  { id: 'sms', label: 'SMS' },
]
const AUDIENCES = [
  { id: 'tenant_owners', label: 'Tenant owners' },
  { id: 'tenant_staff', label: 'All tenant staff' },
  { id: 'freelancers', label: 'Freelancers' },
  { id: 'all_users', label: 'All users' },
]

export default function CommunicationsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('broadcasts')
  const [modal, setModal] = useState<null | 'create' | CommTemplate>(null)
  const [bcastModal, setBcastModal] = useState(false)
  const [form, setForm] = useState(EMPTY_TMPL)
  const [bcastForm, setBcastForm] = useState(EMPTY_BCAST)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(''), 4000)
  }

  const audience = bcastForm.target_filter?.audience ?? 'tenant_owners'

  const { data: templates = [] } = useQuery({
    queryKey: ['admin', 'comms', 'templates'],
    queryFn: () => adminApi.listCommTemplates().then((r) => r.data),
  })
  const { data: broadcasts = [] } = useQuery({
    queryKey: ['admin', 'comms', 'broadcasts'],
    queryFn: () => adminApi.listBroadcasts().then((r) => r.data),
  })
  const { data: recipientPreview } = useQuery({
    queryKey: ['admin', 'comms', 'preview', audience],
    queryFn: () => adminApi.previewBroadcastRecipients(audience).then((r) => r.data),
    enabled: bcastModal,
  })

  const saveMut = useMutation({
    mutationFn: () =>
      modal === 'create'
        ? adminApi.createCommTemplate(form)
        : adminApi.updateCommTemplate((modal as CommTemplate).id, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'comms'] })
      setModal(null)
      showToast('Template saved')
    },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteCommTemplate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'comms'] })
      setDeleteId(null)
    },
  })
  const bcastMut = useMutation({
    mutationFn: () =>
      adminApi.createBroadcast({
        ...bcastForm,
        send_now: true,
        scheduled_at: bcastForm.scheduled_at || null,
      }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['admin', 'comms'] })
      setBcastModal(false)
      showToast(`Broadcast sent to ${res.data.recipient_count ?? 0} recipient(s)`)
    },
    onError: () => showToast('Broadcast failed — check API logs'),
  })
  const resendMut = useMutation({
    mutationFn: (id: string) => adminApi.sendBroadcast(id),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['admin', 'comms'] })
      showToast(`Sent to ${res.data.recipient_count} recipient(s)`)
    },
  })

  const CHANNEL_COLORS: Record<string, string> = {
    email: 'bg-blue-900/30 text-blue-400',
    sms: 'bg-green-900/30 text-green-400',
    whatsapp: 'bg-emerald-900/30 text-emerald-400',
    push: 'bg-purple-900/30 text-purple-300',
    in_app: 'bg-indigo-900/30 text-indigo-300',
    push_only: 'bg-violet-900/30 text-violet-300',
  }

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">
          {toast}
        </div>
      )}

      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Mail className="h-6 w-6 text-amber-400" /> Communication Hub
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Push urgent alerts and marketing messages to tenant owners, staff, and freelancers
        </p>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <div className="flex w-fit gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1">
          {(['templates', 'broadcasts'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${
                tab === t ? 'bg-amber-500 text-black' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        {tab === 'templates' ? (
          <button
            onClick={() => {
              setForm(EMPTY_TMPL)
              setModal('create')
            }}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400"
          >
            <Plus className="h-4 w-4" /> Add Template
          </button>
        ) : (
          <button
            onClick={() => {
              setBcastForm(EMPTY_BCAST)
              setBcastModal(true)
            }}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400"
          >
            <Megaphone className="h-4 w-4" /> Send Broadcast
          </button>
        )}
      </div>

      {tab === 'templates' && (
        <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-xs uppercase tracking-wider text-gray-400">
              <tr>
                {['Name', 'Channel', 'Subject', 'Status', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(templates as CommTemplate[]).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No templates yet
                  </td>
                </tr>
              )}
              {(templates as CommTemplate[]).map((t) => (
                <tr key={t.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CHANNEL_COLORS[t.channel] ?? 'bg-gray-700 text-gray-400'}`}
                    >
                      {t.channel}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{t.subject ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${t.is_active ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-500'}`}
                    >
                      {t.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setForm({
                            name: t.name,
                            channel: t.channel,
                            subject: t.subject ?? '',
                            body: t.body,
                            is_active: t.is_active,
                          })
                          setModal(t)
                        }}
                        className="rounded p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteId(t.id)}
                        className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400"
                      >
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

      {tab === 'broadcasts' && (
        <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-xs uppercase tracking-wider text-gray-400">
              <tr>
                {['Title', 'Channel', 'Status', 'Recipients', 'Created', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(broadcasts as BroadcastItem[]).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    No broadcasts yet — send your first alert above
                  </td>
                </tr>
              )}
              {(broadcasts as BroadcastItem[]).map((b) => (
                <tr key={b.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{b.name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CHANNEL_COLORS[b.channel] ?? 'bg-gray-700 text-gray-400'}`}
                    >
                      {b.channel}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        b.status === 'sent'
                          ? 'bg-green-900/30 text-green-400'
                          : 'bg-yellow-900/30 text-yellow-400'
                      }`}
                    >
                      {b.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{b.recipient_count}</td>
                  <td className="px-4 py-3 text-gray-400">{new Date(b.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    {b.status === 'pending' ? (
                      <button
                        onClick={() => resendMut.mutate(b.id)}
                        className="inline-flex items-center gap-1 rounded bg-amber-500/20 px-2 py-1 text-xs text-amber-300 hover:bg-amber-500/30"
                      >
                        <Send className="h-3 w-3" /> Send
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-lg rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">{modal === 'create' ? 'Add Template' : 'Edit Template'}</h2>
            <div className="space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Template name"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              />
              <select
                value={form.channel}
                onChange={(e) => setForm((f) => ({ ...f, channel: e.target.value }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              >
                {TMPL_CHANNELS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {form.channel === 'email' && (
                <input
                  value={form.subject}
                  onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                  placeholder="Email subject"
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
                />
              )}
              <textarea
                rows={5}
                value={form.body}
                onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
                placeholder="Template body"
                className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              />
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setModal(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300">
                Cancel
              </button>
              <button
                onClick={() => saveMut.mutate()}
                disabled={saveMut.isPending}
                className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {bcastModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-lg rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-1 text-lg font-semibold">Send platform broadcast</h2>
            <p className="mb-4 text-xs text-gray-400">
              {recipientPreview ? `${recipientPreview.count} recipient(s) for selected audience` : 'Loading audience…'}
            </p>
            <div className="space-y-3">
              <input
                value={bcastForm.name}
                onChange={(e) => setBcastForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Alert title (shown on lock screen / bell)"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              />
              <select
                value={bcastForm.channel}
                onChange={(e) => setBcastForm((f) => ({ ...f, channel: e.target.value }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              >
                {BROADCAST_CHANNELS.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
              <select
                value={audience}
                onChange={(e) =>
                  setBcastForm((f) => ({
                    ...f,
                    target_filter: { ...f.target_filter, audience: e.target.value },
                  }))
                }
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              >
                {AUDIENCES.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
              <input
                value={bcastForm.target_filter?.link ?? '/dashboard/notifications'}
                onChange={(e) =>
                  setBcastForm((f) => ({
                    ...f,
                    target_filter: { ...f.target_filter, link: e.target.value },
                  }))
                }
                placeholder="Deep link when tapped (e.g. /dashboard/notifications)"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              />
              <textarea
                rows={4}
                value={bcastForm.body}
                onChange={(e) => setBcastForm((f) => ({ ...f, body: e.target.value }))}
                placeholder="Message body — keep urgent alerts short and actionable"
                className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
              />
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setBcastModal(false)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300">
                Cancel
              </button>
              <button
                onClick={() => bcastMut.mutate()}
                disabled={bcastMut.isPending || !bcastForm.name.trim() || !bcastForm.body.trim()}
                className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                {bcastMut.isPending ? 'Sending…' : 'Send now'}
              </button>
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
              <button onClick={() => setDeleteId(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300">
                Cancel
              </button>
              <button
                onClick={() => deleteMut.mutate(deleteId)}
                disabled={deleteMut.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
