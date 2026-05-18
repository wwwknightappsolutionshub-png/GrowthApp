'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext, DragEndEvent, PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { toast } from 'sonner'
import {
  AlertCircle, Bell, Calendar, CheckCircle2, ChevronLeft, ChevronRight,
  Mail, MessageSquare, Phone, Plus, Search, Trash2, User, Users, X,
} from 'lucide-react'
import { crm } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'

// ── Types ────────────────────────────────────────────────────────────────────

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

interface Deal {
  id: string
  title: string
  stage: string
  value_pence: number
  customer?: { first_name: string; last_name: string | null } | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function initials(c: Customer) {
  return `${c.first_name[0] ?? ''}${c.last_name?.[0] ?? ''}`.toUpperCase()
}

// ── Customer form modal ───────────────────────────────────────────────────────

interface CustomerFormProps {
  customer?: Customer | null
  onClose: () => void
  onSaved: () => void
}

function CustomerForm({ customer, onClose, onSaved }: CustomerFormProps) {
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
    followup_reminder_at: customer?.followup_reminder_at ? customer.followup_reminder_at.slice(0, 16) : '',
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
        followup_reminder_at: form.followup_reminder_at ? new Date(form.followup_reminder_at).toISOString() : null,
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
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to save'),
  })

  const field = (
    label: string,
    key: keyof typeof form,
    type = 'text',
    placeholder = '',
  ) => (
    <div>
      <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </label>
      <input
        type={type}
        value={String(form[key])}
        onChange={(e) => setForm((p) => ({ ...p, [key]: e.target.value }))}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-teal-500/30"
      />
    </div>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-2xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-base font-semibold text-foreground">
            {editing ? 'Edit Customer' : 'Add Customer'}
          </h2>
          <button onClick={onClose} className="rounded p-1 text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-6">
          <div className="grid grid-cols-2 gap-4">
            {field('First name *', 'first_name', 'text', 'Jane')}
            {field('Last name', 'last_name', 'text', 'Smith')}
            {field('Email', 'email', 'email', 'jane@example.com')}
            {field('Phone', 'phone', 'tel', '+44 7700 000000')}
            {field('Address', 'address', 'text', '12 High Street')}
            {field('Postcode', 'postcode', 'text', 'SW1A 1AA')}
            {field('First visit date', 'first_visit_date', 'date')}
            {field('Next visit date', 'next_visit_date', 'date')}
            {field('Follow-up reminder', 'followup_reminder_at', 'datetime-local')}
          </div>

          <div className="mt-4">
            <label className="mb-2 flex cursor-pointer items-center gap-2.5">
              <div
                onClick={() => setForm((p) => ({ ...p, requires_followup: !p.requires_followup }))}
                className={`relative h-5 w-9 rounded-full transition-colors ${form.requires_followup ? 'bg-brand-teal-500' : 'bg-muted'}`}
              >
                <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${form.requires_followup ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm font-medium text-foreground">Requires follow-up</span>
            </label>
          </div>

          <div className="mt-4">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Special comments
            </label>
            <textarea
              value={form.special_comments}
              onChange={(e) => setForm((p) => ({ ...p, special_comments: e.target.value }))}
              rows={2}
              placeholder="Allergies, preferences, important notes…"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-teal-500/30"
            />
          </div>

          <div className="mt-4">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Internal notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
              rows={2}
              placeholder="Team-only notes…"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-teal-500/30"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 border-t border-border px-6 py-4">
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted">
            Cancel
          </button>
          <button
            disabled={!form.first_name.trim() || save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : editing ? 'Save changes' : 'Add customer'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Customer card ─────────────────────────────────────────────────────────────

function CustomerRow({ c, onEdit, onDelete }: { c: Customer; onEdit: () => void; onDelete: () => void }) {
  const needsFollowup = c.requires_followup
  const reminderOverdue = c.followup_reminder_at && new Date(c.followup_reminder_at) < new Date()

  return (
    <tr className="border-b border-border transition-colors hover:bg-muted/30">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-forest-700/10 text-xs font-bold text-brand-forest-700">
            {initials(c)}
          </div>
          <div>
            <p className="font-medium text-foreground">
              {c.first_name} {c.last_name}
            </p>
            <p className="text-xs text-muted-foreground">{c.email || '—'}</p>
          </div>
        </div>
      </td>
      <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
        {c.phone ? (
          <a href={`tel:${c.phone}`} className="flex items-center gap-1 hover:text-brand-teal-600">
            <Phone className="h-3 w-3" /> {c.phone}
          </a>
        ) : '—'}
      </td>
      <td className="hidden px-4 py-3 text-sm lg:table-cell">
        <span className={c.next_visit_date && new Date(c.next_visit_date) < new Date() ? 'font-semibold text-destructive' : 'text-foreground'}>
          {fmt(c.next_visit_date)}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {needsFollowup && (
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${reminderOverdue ? 'bg-destructive/10 text-destructive' : 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400'}`}>
              <Bell className="h-3 w-3" />
              {reminderOverdue ? 'Overdue' : 'Reminder set'}
            </span>
          )}
          {c.special_comments && (
            <span title={c.special_comments} className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
              <MessageSquare className="h-3 w-3" /> Note
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          <button onClick={onEdit} className="rounded p-1.5 text-muted-foreground hover:bg-brand-teal-50 hover:text-brand-teal-700 dark:hover:bg-brand-teal-900/20">
            <User className="h-4 w-4" />
          </button>
          <button onClick={onDelete} className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

// ── Pipeline (kanban) ─────────────────────────────────────────────────────────

const STAGES = ['New', 'Contacted', 'Quoted', 'Booked', 'Completed', 'Lost']
const STAGE_COLORS: Record<string, string> = {
  New: 'border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/40',
  Contacted: 'border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40',
  Quoted: 'border-orange-300 bg-orange-50 dark:border-orange-800 dark:bg-orange-950/40',
  Booked: 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/40',
  Completed: 'border-teal-300 bg-teal-50 dark:border-teal-800 dark:bg-teal-950/40',
  Lost: 'border-border bg-muted/30',
}

function DealCard({ deal }: { deal: Deal }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: deal.id })
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      {...attributes}
      {...listeners}
      className={`rounded-lg border border-border bg-card p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow ${isDragging ? 'opacity-50' : ''}`}
    >
      <p className="text-sm font-medium text-foreground truncate">{deal.title}</p>
      <p className="text-xs text-muted-foreground mt-1">
        {deal.customer?.first_name} {deal.customer?.last_name}
      </p>
      {deal.value_pence > 0 && (
        <p className="text-xs font-semibold text-brand-teal-600 mt-2">{formatCurrency(deal.value_pence)}</p>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = 'customers' | 'pipeline'

export default function CRMPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('customers')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const [editCustomer, setEditCustomer] = useState<Customer | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<Customer | null>(null)

  // Customers
  const { data: custData, isLoading: custLoading } = useQuery({
    queryKey: ['crm', 'customers', page],
    queryFn: () => crm.listCustomers({ page, page_size: 25 }).then((r) => r.data),
    enabled: tab === 'customers',
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => crm.deleteCustomer(id),
    onSuccess: () => {
      toast.success('Customer removed')
      qc.invalidateQueries({ queryKey: ['crm', 'customers'] })
      setDeleteConfirm(null)
    },
    onError: () => toast.error('Failed to remove customer'),
  })

  // Pipeline
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))
  const { data: pipeData, isLoading: pipeLoading } = useQuery({
    queryKey: ['pipeline'],
    queryFn: () => crm.pipeline().then((r) => r.data),
    enabled: tab === 'pipeline',
  })

  const moveMut = useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: string }) =>
      crm.moveDeal(id, { stage, stage_order: 0 }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] }),
    onError: () => toast.error('Failed to move deal'),
  })

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    if (STAGES.includes(over.id as string)) {
      moveMut.mutate({ id: active.id as string, stage: over.id as string })
    }
  }

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
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">CRM</h1>
          <p className="text-sm text-muted-foreground">
            Manage customers, track visits, deals, and follow-ups
          </p>
        </div>
        {tab === 'customers' && (
          <button
            onClick={() => setAddOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-forest-800"
          >
            <Plus className="h-4 w-4" /> Add Customer
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/40 p-1 w-fit">
        {(['customers', 'pipeline'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === t
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t === 'customers' ? <Users className="h-4 w-4" /> : <Calendar className="h-4 w-4" />}
            {t === 'customers' ? 'Customers' : 'Pipeline'}
            {t === 'customers' && custData?.total != null && (
              <span className="rounded-full bg-brand-forest-700/10 px-1.5 py-0.5 text-xs font-semibold text-brand-forest-700">
                {custData.total}
              </span>
            )}
            {t === 'pipeline' && pipeData?.total_deals != null && (
              <span className="rounded-full bg-brand-teal-500/10 px-1.5 py-0.5 text-xs font-semibold text-brand-teal-600">
                {pipeData.total_deals}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── CUSTOMERS TAB ── */}
      {tab === 'customers' && (
        <div className="space-y-4">
          {/* Search */}
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name, email, phone…"
              className="w-full rounded-lg border border-border bg-background py-2 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-teal-500/30"
            />
          </div>

          {/* Followup banner */}
          {(() => {
            const overdue = (custData?.items ?? []).filter(
              (c: Customer) =>
                c.requires_followup &&
                c.followup_reminder_at &&
                new Date(c.followup_reminder_at) < new Date(),
            )
            return overdue.length > 0 ? (
              <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  <strong>{overdue.length}</strong> customer{overdue.length > 1 ? 's' : ''} ha
                  {overdue.length === 1 ? 's' : 've'} an overdue follow-up reminder.
                </span>
              </div>
            ) : null
          })()}

          {/* Table */}
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="min-w-[560px] w-full text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Customer</th>
                  <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground md:table-cell">Phone</th>
                  <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground lg:table-cell">Next visit</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Flags</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-card">
                {custLoading &&
                  [...Array(5)].map((_, i) => (
                    <tr key={i}>
                      <td colSpan={5} className="px-4 py-3">
                        <div className="h-8 animate-pulse rounded bg-muted" />
                      </td>
                    </tr>
                  ))}
                {!custLoading && filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
                      No customers yet. Add your first one →
                    </td>
                  </tr>
                )}
                {filtered.map((c: Customer) => (
                  <CustomerRow
                    key={c.id}
                    c={c}
                    onEdit={() => setEditCustomer(c)}
                    onDelete={() => setDeleteConfirm(c)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {custData && custData.total > 25 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {(page - 1) * 25 + 1}–{Math.min(page * 25, custData.total)} of {custData.total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded p-1 hover:bg-muted disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  disabled={page * 25 >= custData.total}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded p-1 hover:bg-muted disabled:opacity-40"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── PIPELINE TAB ── */}
      {tab === 'pipeline' && (
        <div className="space-y-3">
          {pipeData && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{pipeData.total_deals} deals</span>
              <span>·</span>
              <span className="font-semibold text-brand-teal-600">{formatCurrency(pipeData.total_value_pence)} total value</span>
            </div>
          )}
          {pipeLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-teal-500 border-t-transparent" />
            </div>
          ) : (
            <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
              <div className="flex snap-x gap-4 overflow-x-auto pb-4">
                {STAGES.map((stage) => {
                  const stageDeals = pipeData?.columns?.[stage] ?? []
                  return (
                    <div
                      key={stage}
                      className={`w-[min(15rem,82vw)] flex-shrink-0 snap-start rounded-xl border-2 p-3 ${STAGE_COLORS[stage]}`}
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-foreground">{stage}</h3>
                        <span className="rounded-full bg-card px-2 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">
                          {stageDeals.length}
                        </span>
                      </div>
                      <SortableContext
                        items={stageDeals.map((d: Deal) => d.id)}
                        strategy={verticalListSortingStrategy}
                        id={stage}
                      >
                        <div className="min-h-20 space-y-2">
                          {stageDeals.map((deal: Deal) => (
                            <DealCard key={deal.id} deal={deal} />
                          ))}
                        </div>
                      </SortableContext>
                    </div>
                  )
                })}
              </div>
            </DndContext>
          )}
        </div>
      )}

      {/* Add / Edit modal */}
      {(addOpen || editCustomer) && (
        <CustomerForm
          customer={editCustomer}
          onClose={() => { setAddOpen(false); setEditCustomer(null) }}
          onSaved={() => { setAddOpen(false); setEditCustomer(null) }}
        />
      )}

      {/* Delete confirm */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-foreground">Remove customer?</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              <strong>{deleteConfirm.first_name} {deleteConfirm.last_name}</strong> will be soft-deleted. This cannot be undone.
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
              >
                Cancel
              </button>
              <button
                disabled={deleteMut.isPending}
                onClick={() => deleteMut.mutate(deleteConfirm.id)}
                className="rounded-lg bg-destructive px-4 py-2 text-sm font-semibold text-white hover:bg-destructive/90 disabled:opacity-50"
              >
                {deleteMut.isPending ? 'Removing…' : 'Remove'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
