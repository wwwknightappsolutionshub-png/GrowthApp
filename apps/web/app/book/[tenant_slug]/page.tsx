'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { publicBooking } from '@/lib/api-client'
import { publicBookingSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { formatCurrency } from '@/lib/utils'

const fieldClass = 'w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-emerald-600/30 focus:border-emerald-700'

export default function PublicBookPage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()
  const [form, setForm] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    service_description: '',
    booking_date: '',
    start_time: '09:00',
    slot_id: '',
    service_id: '',
  })

  const { data: widget } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: () => publicBooking.widget(slug).then((r) => r.data),
    enabled: !!slug,
  })

  const { data: availability } = useQuery({
    queryKey: ['public-booking-availability', slug, form.service_id],
    queryFn: () =>
      publicBooking.availability(slug, { service_id: form.service_id || undefined }).then((r) => r.data),
    enabled: !!slug,
  })

  const selectedService = useMemo(
    () => widget?.services?.find((s: { id: string }) => s.id === form.service_id),
    [widget, form.service_id],
  )

  const depositPence = useMemo(() => {
    if (!widget?.deposit_enabled) return 0
    const svcDeposit = selectedService?.deposit_pence
    if (typeof svcDeposit === 'number' && svcDeposit > 0) return svcDeposit
    return widget.default_deposit_pence ?? 0
  }, [widget, selectedService])

  const bookMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        ...form,
        slot_id: form.slot_id || null,
        service_id: form.service_id || null,
        channel: 'widget',
      }
      publicBookingSchema.parse(payload)
      return publicBooking.create(slug, payload).then((r) => r.data)
    },
    onSuccess: (data: {
      message?: string
      manage_url?: string
      payment?: { client_secret?: string; payment_intent_id?: string }
    }) => {
      toast.success(data.message || 'Booking confirmed')
      if (data.payment?.client_secret && data.manage_url) {
        toast.message('Deposit required', {
          description: 'Complete payment from your booking management link.',
        })
      }
      if (data.manage_url) window.location.href = data.manage_url
    },
    onError: () => toast.error('Could not complete booking'),
  })

  const accent = widget?.widget_primary_color || '#166534'

  return (
    <PublicBookShell
      tenantName={widget?.tenant_name || 'Book online'}
      subtitle="Choose a service and time — we will confirm your appointment."
      accent={accent}
    >
      <div className="space-y-4">
        <input
          className={fieldClass}
          placeholder="Your name *"
          value={form.customer_name}
          onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
        />
        <input
          className={fieldClass}
          placeholder="Email *"
          type="email"
          required
          value={form.customer_email}
          onChange={(e) => setForm((f) => ({ ...f, customer_email: e.target.value }))}
        />
        <input
          className={fieldClass}
          placeholder="Phone"
          value={form.customer_phone}
          onChange={(e) => setForm((f) => ({ ...f, customer_phone: e.target.value }))}
        />
        {widget?.services?.length > 0 && (
          <select
            className={fieldClass}
            value={form.service_id}
            onChange={(e) => setForm((f) => ({ ...f, service_id: e.target.value }))}
          >
            <option value="">Select service</option>
            {widget.services.map((s: { id: string; name: string; duration_minutes?: number }) => (
              <option key={s.id} value={s.id}>
                {s.name}
                {s.duration_minutes ? ` (${s.duration_minutes} min)` : ''}
              </option>
            ))}
          </select>
        )}
        {availability?.slots?.length > 0 ? (
          <select
            className={fieldClass}
            value={form.slot_id}
            onChange={(e) => {
              const slot = availability.slots.find((s: { id: string }) => s.id === e.target.value)
              setForm((f) => ({
                ...f,
                slot_id: e.target.value,
                booking_date: slot?.date || f.booking_date,
                start_time: slot?.start?.slice(0, 5) || f.start_time,
              }))
            }}
          >
            <option value="">Available slot *</option>
            {availability.slots.map((s: { id: string; date: string; start: string }) => (
              <option key={s.id} value={s.id}>
                {s.date} {s.start?.slice(0, 5)}
              </option>
            ))}
          </select>
        ) : (
          <>
            <input
              type="date"
              className={fieldClass}
              value={form.booking_date}
              onChange={(e) => setForm((f) => ({ ...f, booking_date: e.target.value }))}
            />
            <input
              type="time"
              className={fieldClass}
              value={form.start_time}
              onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
            />
          </>
        )}
        <textarea
          className={fieldClass}
          placeholder="Anything we should know?"
          rows={3}
          value={form.service_description}
          onChange={(e) => setForm((f) => ({ ...f, service_description: e.target.value }))}
        />
        {depositPence > 0 && (
          <p className="text-xs text-slate-600 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
            A deposit of <strong>{formatCurrency(depositPence)}</strong> secures your slot. You may be asked to pay
            after confirming.
          </p>
        )}
        <button
          type="button"
          disabled={
            bookMutation.isPending ||
            !form.customer_name ||
            !form.customer_email ||
            (!form.booking_date && !form.slot_id)
          }
          onClick={() => bookMutation.mutate()}
          className="w-full py-3.5 rounded-xl text-white font-semibold text-sm disabled:opacity-50 shadow-md"
          style={{ backgroundColor: accent }}
        >
          {bookMutation.isPending ? 'Booking…' : depositPence > 0 ? 'Confirm & secure slot' : 'Confirm booking'}
        </button>
      </div>
    </PublicBookShell>
  )
}
