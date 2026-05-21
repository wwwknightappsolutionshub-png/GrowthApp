'use client'

import { useParams } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { publicBooking } from '@/lib/api-client'
import { toast } from 'sonner'

export default function ManageBookingPage() {
  const { token } = useParams<{ token: string }>()
  const [bookingDate, setBookingDate] = useState('')
  const [startTime, setStartTime] = useState('09:00')

  const cancelMutation = useMutation({
    mutationFn: () => publicBooking.manage(token, { action: 'cancel' }).then((r) => r.data),
    onSuccess: () => toast.success('Booking cancelled'),
    onError: () => toast.error('Could not cancel'),
  })

  const rescheduleMutation = useMutation({
    mutationFn: () =>
      publicBooking
        .manage(token, { action: 'reschedule', booking_date: bookingDate, start_time: startTime })
        .then((r) => r.data),
    onSuccess: () => toast.success('Booking rescheduled'),
    onError: () => toast.error('Could not reschedule'),
  })

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg border p-8 space-y-6">
        <h1 className="text-xl font-bold text-gray-900">Manage your booking</h1>
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-gray-700">Reschedule</h2>
          <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm" value={bookingDate} onChange={(e) => setBookingDate(e.target.value)} />
          <input type="time" className="w-full border rounded-lg px-3 py-2 text-sm" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          <button
            type="button"
            disabled={rescheduleMutation.isPending || !bookingDate}
            onClick={() => rescheduleMutation.mutate()}
            className="w-full py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
          >
            Reschedule
          </button>
        </div>
        <div className="border-t pt-4">
          <button
            type="button"
            disabled={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
            className="w-full py-2 rounded-lg border border-red-300 text-red-600 text-sm font-medium"
          >
            Cancel booking
          </button>
        </div>
      </div>
    </div>
  )
}
