'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ArrowLeft, Calendar } from 'lucide-react'
import { crm } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function CustomerProfilePage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [note, setNote] = useState('')

  const { data: customer, isLoading } = useQuery({
    queryKey: ['crm', 'customer', id],
    queryFn: () => crm.getCustomer(id).then((r) => r.data),
  })

  const { data: activities } = useQuery({
    queryKey: ['crm', 'activities', 'customer', id],
    queryFn: () => crm.listActivities('customer', id).then((r) => r.data),
  })

  const { data: bookings } = useQuery({
    queryKey: ['crm', 'customer', id, 'bookings'],
    queryFn: () => crm.customerBookings(id).then((r) => r.data),
  })

  const addNote = useMutation({
    mutationFn: () =>
      crm.createActivity({
        entity_type: 'customer',
        entity_id: id,
        activity_type: 'note',
        body: note,
      }),
    onSuccess: () => {
      toast.success('Note added')
      setNote('')
      qc.invalidateQueries({ queryKey: ['crm', 'activities', 'customer', id] })
    },
  })

  if (isLoading) {
    return <div className="py-20 text-center text-muted-foreground">Loading…</div>
  }

  if (!customer) {
    return <div className="py-20 text-center text-muted-foreground">Customer not found</div>
  }

  return (
    <div className="space-y-6">
      <Link
        href="/dashboard/crm/customers"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Back to customers
      </Link>

      <div>
        <h1 className="font-display text-2xl font-bold text-foreground">
          {customer.first_name} {customer.last_name}
        </h1>
        <p className="text-sm text-muted-foreground">
          {customer.email} · {customer.phone || 'No phone'}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Activity timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add a note…"
                className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm"
              />
              <button
                type="button"
                disabled={!note.trim() || addNote.isPending}
                onClick={() => addNote.mutate()}
                className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                Add
              </button>
            </div>
            <ul className="max-h-80 space-y-3 overflow-y-auto">
              {(activities ?? []).map((a: { id: string; activity_type: string; body?: string; created_at: string }) => (
                <li key={a.id} className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
                  <span className="text-xs font-semibold uppercase text-muted-foreground">{a.activity_type}</span>
                  <p className="mt-1 text-foreground">{a.body || '—'}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{formatDate(a.created_at)}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-4 w-4" /> Appointments (read-only)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(bookings ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No linked bookings</p>
            ) : (
              <ul className="space-y-2">
                {(bookings as { id: string; booking_date?: string; status: string; service_type?: string }[]).map(
                  (b) => (
                    <li key={b.id} className="rounded-lg border border-border px-3 py-2 text-sm">
                      <p className="font-medium">{b.service_type || 'Booking'}</p>
                      <p className="text-muted-foreground">
                        {b.booking_date ? formatDate(b.booking_date) : '—'} · {b.status}
                      </p>
                    </li>
                  ),
                )}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
