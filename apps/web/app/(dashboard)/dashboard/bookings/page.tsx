'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { useState } from 'react'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import { Calendar, Clock, User } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  confirmed: 'bg-green-50 text-green-700',
  pending: 'bg-yellow-50 text-yellow-700',
  cancelled: 'bg-red-50 text-red-700',
  completed: 'bg-teal-50 text-teal-700',
}

export default function BookingsPage() {
  const [page, setPage] = useState(1)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['bookings', { page }],
    queryFn: () => bookings.list({ page, page_size: 25 }).then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      bookings.update(id, { status }),
    onSuccess: () => {
      toast.success('Booking updated')
      qc.invalidateQueries({ queryKey: ['bookings'] })
    },
    onError: () => toast.error('Failed to update booking'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Bookings</h1>
          <p className="text-muted-foreground text-sm">Manage your confirmed appointments</p>
        </div>
        <span className="text-sm text-muted-foreground">{data?.total ?? 0} total</span>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid gap-4">
          {data?.items?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-12 text-center text-brand-teal-100/60">
              <Calendar className="w-10 h-10 mx-auto mb-3 text-brand-teal-300/70" />
              <p className="font-medium">No bookings yet</p>
              <p className="text-sm mt-1">Bookings created via your pipeline or public booking form will appear here</p>
            </div>
          )}
          {data?.items?.map((booking: any) => (
            <div key={booking.id} className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[booking.status] || 'bg-gray-100 text-muted-foreground'}`}>
                      {booking.status}
                    </span>
                    {booking.deposit_required_pence > 0 && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${booking.deposit_paid_pence >= booking.deposit_required_pence ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'}`}>
                        Deposit {booking.deposit_paid_pence >= booking.deposit_required_pence ? 'paid' : 'unpaid'}
                      </span>
                    )}
                  </div>
                  <p className="font-semibold text-white">{booking.customer_name}</p>
                  {booking.service_description && (
                    <p className="text-sm text-brand-teal-100/70 mt-0.5">{booking.service_description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-sm text-brand-teal-100/70">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      {booking.booking_date}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      {booking.start_time}
                    </span>
                    {(booking.customer_phone || booking.customer_email) && (
                      <span className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5" />
                        {booking.customer_phone || booking.customer_email}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  {booking.status === 'confirmed' && (
                    <button
                      onClick={() => updateMutation.mutate({ id: booking.id, status: 'completed' })}
                      disabled={updateMutation.isPending}
                      className="text-xs bg-brand-forest-700 text-brand-forest-foreground px-3 py-1.5 rounded-lg hover:bg-brand-forest-800 disabled:opacity-50"
                    >
                      Mark Complete
                    </button>
                  )}
                  {booking.status === 'confirmed' && (
                    <button
                      onClick={() => updateMutation.mutate({ id: booking.id, status: 'cancelled' })}
                      disabled={updateMutation.isPending}
                      className="text-xs border border-red-200 text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-50"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total > 25 && (
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm border border-brand-forest-700 rounded-lg disabled:opacity-40 hover:bg-brand-forest-900"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">Page {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={data.items.length < 25}
            className="px-4 py-2 text-sm border border-brand-forest-700 rounded-lg disabled:opacity-40 hover:bg-brand-forest-900"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
