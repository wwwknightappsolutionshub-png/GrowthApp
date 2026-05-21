'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  AlertCircle,
  Bell,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Phone,
  Plus,
  Search,
  Trash2,
  User,
  X,
} from 'lucide-react'
import { crm } from '@/lib/api-client'

interface Customer {
  id: string
  first_name: string
  last_name: string | null
  email: string | null
  phone: string | null
  address: string | null
  postcode: string | null
  notes: string | null
  first_visit_date: string | null
  next_visit_date: string | null
  requires_followup: boolean
  followup_reminder_at: string | null
  special_comments: string | null
  created_at: string
}

function fmt(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function initials(c: Customer) {
  return `${c.first_name[0] ?? ''}${c.last_name?.[0] ?? ''}`.toUpperCase()
}

function CustomerForm({
  customer,
  onClose,
  onSaved,
}: {
  customer?: Customer | null
  onClose: () => void
  onSaved: () => void
}) {
  const editing = !!customer
  const [form, setForm] = useState({
    first_name: customer?.first_name ?? '',
    last_name: customer?.last_name ?? '',
    email: customer?.email ?? '',
    phone: customer?.phone ?? '',
    address: customer?.address ?? '',
    postcode: customer?.postcode ?? '',
    first_visit_date: customer?.first_visit_date ? customer.first_visit_date.slice(0, 10) : '',
    next_visit_date: customer?.next_visit_date ? customer.next_visit_date.slice(0, 10) : '',
    requires_followup: customer?.requires_followup ?? false,
    followup_reminder_at: customer?.followup_reminder_at
      ? customer.followup_reminder_at.slice(0, 16)
      : '',
    special_comments: customer?.special_comments ?? '',
    notes: customer?.notes ?? '',
  })

  const qc = useQueryClient()
  const save = useMutation({
    mutationFn: () => {
      const payload = {
        ...form,
        first_visit_date: form.first_visit_date ? new Date(form.first_visit_date).toISOString() : null,
        next_visit_date: form.next_visit_date ? new Date(form.next_visit_date).toISOString() : null,
        followup_reminder_at: form.followup_reminder_at
          ? new Date(form.followup_reminder_at).toISOString()
          : null,
      }
      return editing
        ? crm.updateCustomer(customer!.id, payload)
        : crm.createCustomer(payload)
    },
    onSuccess: () => {
      toast.success(editing ? 'Customer updated' : 'Customer added')
      qc.invalidateQueries({ queryKey: ['crm', 'customers'] })
      onSaved()
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e?.response?.data?.detail || 'Failed to save'),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-base font-semibold">{editing ? 'Edit Customer' : 'Add Customer'}</h2>
          <button type="button" onClick={onClose}>
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 p-6">
          <div className="grid grid-cols-2 gap-4">
            {(['first_name', 'last_name', 'email', 'phone', 'address', 'postcode'] as const).map((k) => (
              <div key={k}>
                <label className="mb-1 block text-xs font-semibold uppercase text-muted-foreground">
                  {k.replace('_', ' ')}
                </label>
                <input
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                  value={String(form[k])}
                  onChange={(e) => setForm((p) => ({ ...p, [k]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          <button
            type="button"
            disabled={!form.first_name.trim() || save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function CustomersList() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const [editCustomer, setEditCustomer] = useState<Customer | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<Customer | null>(null)

  const { data: custData, isLoading: custLoading } = useQuery({
    queryKey: ['crm', 'customers', page],
    queryFn: () => crm.listCustomers({ page, page_size: 25 }).then((r) => r.data),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => crm.deleteCustomer(id),
    onSuccess: () => {
      toast.success('Customer removed')
      qc.invalidateQueries({ queryKey: ['crm', 'customers'] })
      setDeleteConfirm(null)
    },
  })

  const filtered = (custData?.items ?? []).filter((c: Customer) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
      c.email?.toLowerCase().includes(q) ||
      c.phone?.includes(q)
    )
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">Customers</h1>
          <p className="text-sm text-muted-foreground">Profiles, visits, and follow-ups</p>
        </div>
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white"
        >
          <Plus className="h-4 w-4" /> Add Customer
        </button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search name, email, phone…"
          className="w-full rounded-lg border border-border bg-background py-2 pl-10 pr-4 text-sm"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="min-w-[560px] w-full text-sm">
          <thead className="border-b border-border bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-muted-foreground">
                Customer
              </th>
              <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase text-muted-foreground md:table-cell">
                Phone
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-muted-foreground">
                Flags
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-muted-foreground">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border bg-card">
            {custLoading &&
              [...Array(5)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={4} className="px-4 py-3">
                    <div className="h-8 animate-pulse rounded bg-muted" />
                  </td>
                </tr>
              ))}
            {!custLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-muted-foreground">
                  No customers yet.
                </td>
              </tr>
            )}
            {filtered.map((c: Customer) => (
              <tr key={c.id} className="hover:bg-muted/30">
                <td className="px-4 py-3">
                  <Link href={`/dashboard/crm/customers/${c.id}`} className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-forest-700/10 text-xs font-bold text-brand-forest-700">
                      {initials(c)}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">
                        {c.first_name} {c.last_name}
                      </p>
                      <p className="text-xs text-muted-foreground">{c.email || '—'}</p>
                    </div>
                  </Link>
                </td>
                <td className="hidden px-4 py-3 md:table-cell">{c.phone || '—'}</td>
                <td className="px-4 py-3">
                  {c.requires_followup && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">
                      <Bell className="h-3 w-3" /> Follow-up
                    </span>
                  )}
                  {c.special_comments && (
                    <span className="ml-1 inline-flex items-center gap-1 text-xs text-muted-foreground">
                      <MessageSquare className="h-3 w-3" />
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button type="button" onClick={() => setEditCustomer(c)} className="rounded p-1.5 hover:bg-muted">
                    <User className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteConfirm(c)}
                    className="rounded p-1.5 hover:bg-destructive/10 text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {custData && custData.total > 25 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Page {page} · {custData.total} total
          </span>
          <div className="flex gap-2">
            <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              disabled={page * 25 >= custData.total}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {(addOpen || editCustomer) && (
        <CustomerForm
          customer={editCustomer}
          onClose={() => {
            setAddOpen(false)
            setEditCustomer(null)
          }}
          onSaved={() => {
            setAddOpen(false)
            setEditCustomer(null)
          }}
        />
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6">
            <h3 className="font-semibold">Remove customer?</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {deleteConfirm.first_name} {deleteConfirm.last_name}
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={() => setDeleteConfirm(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="rounded-lg bg-destructive px-4 py-2 text-sm text-white"
                onClick={() => deleteMut.mutate(deleteConfirm.id)}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
