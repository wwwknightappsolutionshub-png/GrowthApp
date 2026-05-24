'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ArrowLeft, Calendar, ExternalLink, Zap } from 'lucide-react'
import { CustomerLoyaltyPanel } from '@/components/membership-rewards/CustomerLoyaltyPanel'
import { crm } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'
import { recurrencyLabel } from '@/components/quotes/RecurrencySelect'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CrmEntityTimeline } from '@/components/crm/CrmEntityTimeline'

export default function CustomerProfilePage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [note, setNote] = useState('')

  const { data: customer, isLoading } = useQuery({
    queryKey: ['crm', 'customer', id],
    queryFn: () => crm.getCustomer(id).then((r) => r.data),
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
      qc.invalidateQueries({ queryKey: ['crm', 'timeline', 'customer', id] })
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
            <p className="text-xs text-muted-foreground">
              Notes, emails/SMS from messaging, and automation runs
            </p>
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
            <CrmEntityTimeline entityType="customer" entityId={id} />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <CustomerLoyaltyPanel customerId={id} />
          {(customer.service_recurrency || customer.service_renewal_date) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Service renewal</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-1">
                <p>
                  <span className="text-muted-foreground">Recurrency:</span>{' '}
                  {recurrencyLabel(customer.service_recurrency)}
                </p>
                <p>
                  <span className="text-muted-foreground">Next renewal:</span>{' '}
                  {customer.service_renewal_date ? formatDate(customer.service_renewal_date) : '—'}
                </p>
                <p className="text-xs text-muted-foreground">
                  You will receive an email 7 days before this date.
                </p>
              </CardContent>
            </Card>
          )}
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
                        <Link
                          href={`/dashboard/bookings`}
                          className="mt-1 inline-flex items-center gap-1 text-xs text-brand-teal-600 hover:underline"
                        >
                          Open in bookings <ExternalLink className="h-3 w-3" />
                        </Link>
                      </li>
                    ),
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Zap className="h-4 w-4" /> Integrations
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>
                Stage changes on the pipeline board fire{' '}
                <code className="text-xs">lead_stage_changed</code> and{' '}
                <code className="text-xs">deal_stage_changed</code> automation events.
              </p>
              <Link
                href="/dashboard/automations"
                className="mt-3 inline-flex items-center gap-1 font-medium text-brand-teal-600 hover:underline"
              >
                Manage automations <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
