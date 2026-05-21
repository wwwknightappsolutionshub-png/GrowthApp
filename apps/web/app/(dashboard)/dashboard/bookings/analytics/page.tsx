'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'

export default function BookingAnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['bookings', 'analytics'],
    queryFn: () => bookings.getAnalytics({ days: 30 }).then((r) => r.data),
  })

  const stats = [
    { label: 'Total bookings', value: data?.total_bookings ?? 0 },
    { label: 'Completed', value: data?.completed ?? 0 },
    { label: 'Cancelled', value: data?.cancelled ?? 0 },
    { label: 'No-shows', value: data?.no_show ?? 0 },
    { label: 'Cancellation rate', value: `${data?.cancellation_rate ?? 0}%` },
    { label: 'No-show rate', value: `${data?.no_show_rate ?? 0}%` },
    { label: 'Utilization', value: `${data?.utilization_rate ?? 0}%` },
    { label: 'Deposits collected', value: `£${((data?.total_deposit_pence ?? 0) / 100).toFixed(2)}` },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">← Bookings</Link>
        <h1 className="text-2xl font-bold text-foreground">Booking analytics</h1>
      </div>
      {isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((s) => (
              <div key={s.label} className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-4">
                <p className="text-xs text-brand-teal-100/60">{s.label}</p>
                <p className="text-2xl font-bold text-white mt-1">{s.value}</p>
              </div>
            ))}
          </div>
          {data?.bookings_by_channel?.length > 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6">
              <h2 className="font-semibold text-white mb-3">By channel</h2>
              <ul className="space-y-2 text-sm text-brand-teal-100/80">
                {data.bookings_by_channel.map((c: { channel: string; count: number }) => (
                  <li key={c.channel} className="flex justify-between">
                    <span>{c.channel}</span>
                    <span>{c.count}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
