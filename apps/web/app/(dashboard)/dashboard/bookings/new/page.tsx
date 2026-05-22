'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { CalendarPlus } from 'lucide-react'
import { auth, bookings, tenants } from '@/lib/api-client'
import { BookingForm, type BookingFormValues } from '@/components/bookings/BookingForm'
import { BookingsPanel, BookingsSubpageLayout } from '@/components/bookings/BookingsSubpageLayout'

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

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

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
    <BookingsSubpageLayout
      tenantName={tenant?.name}
      userName={me?.full_name}
      subtitle="Create a booking for a client — linked to CRM automatically"
    >
      <BookingsPanel>
        <h2 className="text-lg font-bold text-white flex items-center justify-center gap-2 mb-4">
          <CalendarPlus className="w-5 h-5 text-brand-teal-300" />
          New booking
        </h2>
        <BookingForm values={form} onChange={setForm} />
        <button
          type="button"
          disabled={!form.customer_name || !form.booking_date || create.isPending}
          onClick={() => create.mutate()}
          className="mt-6 w-full py-3 rounded-xl bg-brand-teal-600 hover:bg-brand-teal-500 text-white font-semibold text-sm disabled:opacity-50"
        >
          {create.isPending ? 'Saving…' : 'Create booking'}
        </button>
      </BookingsPanel>
    </BookingsSubpageLayout>
  )
}
