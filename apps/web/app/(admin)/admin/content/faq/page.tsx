'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, GripVertical, Eye, EyeOff, Save, X } from 'lucide-react'
import { adminApiClient } from '@/lib/api-client'

interface FaqItem {
  id: string
  question: string
  answer: string
  sort_order: number
  is_active: boolean
}

const api = {
  list: () => adminApiClient.get<FaqItem[]>('/content/faq').then((r) => r.data),
  create: (body: Omit<FaqItem, 'id'>) => adminApiClient.post('/content/faq', body),
  update: (id: string, body: Omit<FaqItem, 'id'>) => adminApiClient.put(`/content/faq/${id}`, body),
  delete: (id: string) => adminApiClient.delete(`/content/faq/${id}`),
}

const EMPTY: Omit<FaqItem, 'id'> = { question: '', answer: '', sort_order: 0, is_active: true }

export default function FaqAdminPage() {
  const qc = useQueryClient()
  const { data: items = [], isLoading } = useQuery({ queryKey: ['admin-faq'], queryFn: api.list })
  const [editing, setEditing] = useState<FaqItem | null>(null)
  const [creating, setCreating] = useState(false)
  const [draft, setDraft] = useState<Omit<FaqItem, 'id'>>(EMPTY)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-faq'] })

  const saveMut = useMutation({
    mutationFn: () => editing ? api.update(editing.id, draft) : api.create(draft),
    onSuccess: () => { invalidate(); setEditing(null); setCreating(false); setDraft(EMPTY) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(id),
    onSuccess: invalidate,
  })

  const toggleMut = useMutation({
    mutationFn: (item: FaqItem) => api.update(item.id, { ...item, is_active: !item.is_active }),
    onSuccess: invalidate,
  })

  function startEdit(item: FaqItem) {
    setEditing(item)
    setDraft({ question: item.question, answer: item.answer, sort_order: item.sort_order, is_active: item.is_active })
    setCreating(false)
  }

  function startCreate() {
    setCreating(true)
    setEditing(null)
    setDraft(EMPTY)
  }

  function cancel() { setEditing(null); setCreating(false); setDraft(EMPTY) }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">FAQ Management</h1>
          <p className="mt-1 text-sm text-white/50">Edit questions and answers shown on the landing page.</p>
        </div>
        <button
          onClick={startCreate}
          className="flex items-center gap-2 rounded-lg bg-brand-teal-400 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-300"
        >
          <Plus className="h-4 w-4" /> Add FAQ
        </button>
      </div>

      {/* Edit / Create form */}
      {(editing || creating) && (
        <div className="rounded-xl border border-white/10 bg-gray-900 p-5 space-y-4">
          <h2 className="font-semibold text-white">{creating ? 'New FAQ Item' : 'Edit FAQ Item'}</h2>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Question *</label>
            <input
              value={draft.question}
              onChange={(e) => setDraft({ ...draft, question: e.target.value })}
              className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
              placeholder="What question does this answer?"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Answer *</label>
            <textarea
              rows={4}
              value={draft.answer}
              onChange={(e) => setDraft({ ...draft, answer: e.target.value })}
              className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
              placeholder="The answer to display…"
            />
          </div>
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Sort order</label>
              <input
                type="number" value={draft.sort_order}
                onChange={(e) => setDraft({ ...draft, sort_order: Number(e.target.value) })}
                className="w-24 rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-white/70 mt-4 cursor-pointer">
              <input
                type="checkbox" checked={draft.is_active}
                onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
                className="rounded"
              />
              Active (visible on site)
            </label>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => saveMut.mutate()}
              disabled={saveMut.isPending || !draft.question || !draft.answer}
              className="flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-forest-600 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" />
              {saveMut.isPending ? 'Saving…' : 'Save'}
            </button>
            <button onClick={cancel} className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm text-white/60 hover:text-white">
              <X className="h-3.5 w-3.5" /> Cancel
            </button>
          </div>
        </div>
      )}

      {/* FAQ list */}
      {isLoading ? (
        <p className="text-white/50 text-sm">Loading…</p>
      ) : (
        <div className="divide-y divide-white/5 rounded-xl border border-white/10 bg-gray-900">
          {items.map((item) => (
            <div key={item.id} className="flex items-start gap-4 p-5">
              <GripVertical className="mt-0.5 h-4 w-4 shrink-0 text-white/20" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${item.is_active ? 'bg-green-400' : 'bg-gray-500'}`} />
                  <p className="font-medium text-white text-sm">{item.question}</p>
                </div>
                <p className="mt-1 text-xs text-white/50 line-clamp-2">{item.answer}</p>
                <p className="mt-1 text-[10px] text-white/30">Order: {item.sort_order}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => toggleMut.mutate(item)}
                  className="rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white"
                  title={item.is_active ? 'Deactivate' : 'Activate'}
                >
                  {item.is_active ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
                <button
                  onClick={() => startEdit(item)}
                  className="rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  onClick={() => { if (confirm('Delete this FAQ item?')) deleteMut.mutate(item.id) }}
                  className="rounded p-1.5 text-red-400/60 hover:bg-red-400/10 hover:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <p className="px-5 py-10 text-center text-sm text-white/30">No FAQ items yet. Click "Add FAQ" to create one.</p>
          )}
        </div>
      )}
    </div>
  )
}
