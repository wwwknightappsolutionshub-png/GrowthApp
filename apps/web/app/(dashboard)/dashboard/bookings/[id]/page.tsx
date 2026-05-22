'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { bookings, auth, tenants } from '@/lib/api-client'
import { BookingForm, type BookingFormValues } from '@/components/bookings/BookingForm'
import { formatDate } from '@/lib/utils'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

export default function BookingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

  const { data: booking, isLoading } = useQuery({
    queryKey: ['bookings', id],
    queryFn: () => bookings.get(id!).then((r) => r.data),
    enabled: !!id,
  })

  const [form, setForm] = useState<BookingFormValues | null>(null)

  useEffect(() => {
    if (booking && !form) {
      setForm({
        customer_name: booking.customer_name,
        customer_email: booking.customer_email ?? '',
        customer_phone: booking.customer_phone ?? '',
        customer_id: booking.customer_id ?? '',
        service_id: booking.service_id ?? '',
        staff_id: booking.staff_id ?? '',
        slot_id: booking.slot_id ?? '',
        booking_date: booking.booking_date?.slice(0, 10) ?? '',
        start_time: booking.start_time?.slice(0, 5) ?? '09:00',
        service_description: booking.service_description ?? '',
        notes: booking.notes ?? '',
        status: booking.status,
        notify_customer: true,
      })
    }
  }, [booking, form])

  const save = useMutation({
    mutationFn: () =>
      bookings.update(id!, {
        booking_date: form!.booking_date,
        start_time: form!.start_time.length === 5 ? `${form!.start_time}:00` : form!.start_time,
        status: form!.status,
        notes: form!.notes || null,
        slot_id: form!.slot_id || null,
        staff_id: form!.staff_id || null,
        service_id: form!.service_id || null,
        notify_customer: form!.notify_customer,
        notify_channels: ['email', 'in_app'],
      }),
    onSuccess: () => {
      toast.success('Booking updated')
      qc.invalidateQueries({ queryKey: ['bookings'] })
    },
    onError: () => toast.error('Update failed'),
  })

  const remove = useMutation({
    mutationFn: () => bookings.delete(id!),
    onSuccess: () => {
      toast.success('Booking deleted')
      router.push('/dashboard/bookings')
    },
    onError: () => toast.error('Delete failed'),
  })

  const feedback = useMutation({
    mutationFn: (channels: string[]) => bookings.requestFeedback(id!, channels),
    onSuccess: () => toast.success('Feedback request sent'),
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not send feedback request'),
  })

  if (isLoading || !form) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Edit booking, notify customer, or request post-visit feedback"
      />
      <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
        ← Bookings hub
      </Link>
      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6">
        <h1 className="text-xl font-bold text-white">{booking.customer_name}</h1>
        <p className="text-sm text-brand-teal-100/65 mt-1">
          {formatDate(booking.booking_date)} · {booking.start_time?.slice(0, 5)} · {booking.status}
        </p>
        {booking.customer_id && (
          <Link
            href={`/dashboard/crm/customers/${booking.customer_id}`}
            className="text-xs text-brand-teal-300 hover:underline mt-2 inline-block"
          >
            View in CRM →
          </Link>
        )}
      </div>
      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6">
        <BookingForm values={form} onChange={setForm} showStatus showNotify />
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => save.mutate()}
            disabled={save.isPending}
            className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold"
          >
            Save changes
          </button>
          {booking.status === 'completed' && !booking.feedback_submitted_at && (
            <button
              type="button"
              onClick={() => feedback.mutate(['email', 'in_app'])}
              disabled={feedback.isPending}
              className="px-4 py-2 rounded-lg border border-brand-teal-400/40 text-brand-teal-100 text-sm"
            >
              Request rating (email + in-app)
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              if (confirm('Permanently delete this booking? This cannot be undone.')) remove.mutate()
            }}
            className="px-4 py-2 rounded-lg border border-red-500/40 text-red-200 text-sm"
          >
            Delete booking
          </button>
        </div>
      </div>
    </div>
  )
}
