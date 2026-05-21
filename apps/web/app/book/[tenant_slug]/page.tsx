'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { publicBooking } from '@/lib/api-client'
import { publicBookingSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'

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
    queryKey: ['public-booking-availability', slug],
    queryFn: () => publicBooking.availability(slug).then((r) => r.data),
    enabled: !!slug,
  })

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
    onSuccess: (data) => {
      toast.success(data.message || 'Booking confirmed')
      if (data.manage_url) window.location.href = data.manage_url
    },
    onError: () => toast.error('Could not complete booking'),
  })

  const accent = widget?.widget_primary_color || '#166534'

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          {widget?.tenant_name || 'Book online'}
        </h1>
        <p className="text-sm text-gray-500 mb-6">Choose a time and we will confirm your appointment.</p>

        <div className="space-y-4">
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Your name *"
            value={form.customer_name}
            onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
          />
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Email"
            type="email"
            value={form.customer_email}
            onChange={(e) => setForm((f) => ({ ...f, customer_email: e.target.value }))}
          />
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Phone"
            value={form.customer_phone}
            onChange={(e) => setForm((f) => ({ ...f, customer_phone: e.target.value }))}
          />
          {widget?.services?.length > 0 && (
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.service_id}
              onChange={(e) => setForm((f) => ({ ...f, service_id: e.target.value }))}
            >
              <option value="">Select service</option>
              {widget.services.map((s: { id: string; name: string }) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          )}
          <input
            type="date"
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={form.booking_date}
            onChange={(e) => setForm((f) => ({ ...f, booking_date: e.target.value }))}
          />
          {availability?.slots?.length > 0 ? (
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm"
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
              <option value="">Available slot</option>
              {availability.slots.map((s: { id: string; date: string; start: string }) => (
                <option key={s.id} value={s.id}>
                  {s.date} {s.start?.slice(0, 5)}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="time"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={form.start_time}
              onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
            />
          )}
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="What do you need?"
            rows={3}
            value={form.service_description}
            onChange={(e) => setForm((f) => ({ ...f, service_description: e.target.value }))}
          />
          <button
            type="button"
            disabled={bookMutation.isPending || !form.customer_name || !form.booking_date}
            onClick={() => bookMutation.mutate()}
            className="w-full py-3 rounded-xl text-white font-semibold text-sm disabled:opacity-50"
            style={{ backgroundColor: accent }}
          >
            {bookMutation.isPending ? 'Booking…' : 'Confirm booking'}
          </button>
        </div>
      </div>
    </div>
  )
}
