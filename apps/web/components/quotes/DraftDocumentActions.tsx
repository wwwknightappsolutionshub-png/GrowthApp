'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail, Pencil, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { crm } from '@/lib/api-client'
import { inputClass, labelClass, lineItemFromPounds } from '@/components/quotes/QuoteInvoiceForm'

type Kind = 'quote' | 'invoice'

type Api = {
  create: (data: object) => Promise<unknown>
  update: (id: string, data: object) => Promise<unknown>
  delete: (id: string) => Promise<unknown>
  send?: (id: string) => Promise<unknown>
}

export function DraftDocumentCreatePanel({
  kind,
  api,
  listQueryKey,
}: {
  kind: Kind
  api: Api
  listQueryKey: string[]
}) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [customerId, setCustomerId] = useState('')
  const [title, setTitle] = useState('')
  const [amount, setAmount] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [validUntil, setValidUntil] = useState('')
  const [sendEmail, setSendEmail] = useState(false)

  const { data: customers } = useQuery({
    queryKey: ['crm', 'customers', kind, 'picker'],
    queryFn: () => crm.listCustomers({ page: 1, page_size: 100 }).then((r) => r.data),
    enabled: open,
  })

  const create = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        customer_id: customerId,
        title: title || (kind === 'quote' ? 'Quote' : 'Invoice'),
        items: [lineItemFromPounds(title || 'Service', amount)],
      }
      if (kind === 'invoice' && dueDate) payload.due_date = dueDate
      if (kind === 'quote' && validUntil) payload.valid_until = validUntil
      const res = (await api.create(payload)) as { data: { id: string } }
      if (sendEmail && api.send && res.data?.id) {
        await api.send(res.data.id)
      }
      return res
    },
    onSuccess: () => {
      toast.success(
        sendEmail
          ? kind === 'quote'
            ? 'Quote created and emailed'
            : 'Invoice created and emailed'
          : kind === 'quote'
            ? 'Quote created'
            : 'Invoice created',
      )
      setOpen(false)
      setTitle('')
      setAmount('')
      setCustomerId('')
      setDueDate('')
      setValidUntil('')
      setSendEmail(false)
      qc.invalidateQueries({ queryKey: listQueryKey })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not create'),
  })

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 rounded-lg bg-brand-teal-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500"
      >
        <Plus className="w-4 h-4" />
        New {kind}
      </button>
      {open && (
        <div className="w-full rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 space-y-3">
          <div>
            <label className={labelClass}>Customer</label>
            <select className={inputClass} value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
              <option value="">Select customer</option>
              {(customers?.items ?? []).map((c: { id: string; first_name: string; last_name?: string }) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name ?? ''}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Title</label>
            <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Description" />
          </div>
          <div>
            <label className={labelClass}>Amount (£)</label>
            <input
              className={inputClass}
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          {kind === 'invoice' && (
            <div>
              <label className={labelClass}>Due date</label>
              <input className={inputClass} type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
          )}
          {kind === 'quote' && (
            <div>
              <label className={labelClass}>Valid until</label>
              <input className={inputClass} type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
            </div>
          )}
          {api.send && (
            <label className="flex items-center gap-2 text-sm text-brand-teal-100/80">
              <input
                type="checkbox"
                checked={sendEmail}
                onChange={(e) => setSendEmail(e.target.checked)}
                className="rounded border-brand-forest-600"
              />
              <Mail className="w-3.5 h-3.5" />
              Send by email after create
            </label>
          )}
          <button
            type="button"
            disabled={!customerId || create.isPending}
            onClick={() => create.mutate()}
            className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            Create draft
          </button>
        </div>
      )}
    </div>
  )
}

export function DraftRowActions({
  id,
  status,
  title,
  kind,
  api,
  listQueryKey,
}: {
  id: string
  status: string
  title: string
  kind: Kind
  api: Api
  listQueryKey: string[]
}) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(title)

  const update = useMutation({
    mutationFn: () => api.update(id, { title: editTitle }),
    onSuccess: () => {
      toast.success('Updated')
      setEditing(false)
      qc.invalidateQueries({ queryKey: listQueryKey })
    },
    onError: () => toast.error('Update failed'),
  })

  const remove = useMutation({
    mutationFn: () => api.delete(id),
    onSuccess: () => {
      toast.success('Deleted')
      qc.invalidateQueries({ queryKey: listQueryKey })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Delete failed'),
  })

  if (status !== 'draft') return null

  if (editing) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <input
          className={`${inputClass} max-w-[180px]`}
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
        />
        <button
          type="button"
          onClick={() => update.mutate()}
          className="text-xs text-brand-teal-300 hover:underline"
        >
          Save
        </button>
        <button type="button" onClick={() => setEditing(false)} className="text-xs text-brand-teal-100/50 hover:underline">
          Cancel
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <button type="button" onClick={() => setEditing(true)} className="text-xs text-brand-teal-300 hover:underline inline-flex items-center gap-0.5">
        <Pencil className="w-3 h-3" /> Edit
      </button>
      <button
        type="button"
        onClick={() => {
          if (confirm(`Delete this draft ${kind}?`)) remove.mutate()
        }}
        className="text-xs text-red-300 hover:underline inline-flex items-center gap-0.5"
      >
        <Trash2 className="w-3 h-3" /> Delete
      </button>
    </div>
  )
}
