'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { bookings } from '@/lib/api-client'
import { BookingForm, type BookingFormValues } from '@/components/bookings/BookingForm'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

const empty: BookingFormValues = {
  customer_name: '',
  customer_email: '',
  customer_phone: '',
  customer_id: '',
  service_id: '',
  staff_id: '',
  slot_id: '',
  booking_date: new Date().toISOString().slice(0, 10),
  start_time: '09:00',
  service_description: '',
  notes: '',
  status: 'confirmed',
  notify_customer: false,
}

export default function NewBookingPage() {
  const router = useRouter()
  const [form, setForm] = useState<BookingFormValues>(empty)

  const create = useMutation({
    mutationFn: () =>
      bookings.create({
        customer_name: form.customer_name,
        customer_email: form.customer_email || null,
        customer_phone: form.customer_phone || null,
        customer_id: form.customer_id || null,
        service_id: form.service_id || null,
        staff_id: form.staff_id || null,
        slot_id: form.slot_id || null,
        booking_date: form.booking_date,
        start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
        service_description: form.service_description || null,
        notes: form.notes || null,
        channel: 'dashboard',
      }),
    onSuccess: (res) => {
      toast.success('Booking created')
      router.push(`/dashboard/bookings/${res.data.id}`)
    },
    onError: () => toast.error('Could not create booking'),
  })

  return (
    <div className="space-y-6 max-w-2xl">
      <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
        ← Bookings
      </Link>
      <TenantWelcomeHeader subtitle="Create a booking for a client — linked to CRM automatically" />
      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6">
        <BookingForm values={form} onChange={setForm} />
        <button
          type="button"
          disabled={!form.customer_name || !form.booking_date || create.isPending}
          onClick={() => create.mutate()}
          className="mt-6 w-full py-3 rounded-xl bg-brand-forest-700 text-white font-semibold text-sm disabled:opacity-50 hover:bg-brand-forest-600"
        >
          {create.isPending ? 'Saving…' : 'Create booking'}
        </button>
      </div>
    </div>
  )
}
