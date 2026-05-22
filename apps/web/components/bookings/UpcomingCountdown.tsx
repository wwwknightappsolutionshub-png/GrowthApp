'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import { bookings } from '@/lib/api-client'

function formatCountdown(seconds: number): string {
  if (seconds < 3600) return `${Math.max(1, Math.floor(seconds / 60))} min`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  return `${d}d ${h}h`
}

export function UpcomingCountdown() {
  const { data } = useQuery({
    queryKey: ['bookings', 'upcoming'],
    queryFn: () => bookings.upcoming(8).then((r) => r.data),
    refetchInterval: 60_000,
  })

  const items = data?.items ?? []
  if (items.length === 0) return null

  return (
    <section className="rounded-2xl border border-brand-teal-400/30 bg-brand-forest-950 p-5">
      <h2 className="text-sm font-bold text-white flex items-center gap-2 mb-4">
        <Clock className="w-4 h-4 text-brand-teal-300" />
        Upcoming sessions
      </h2>
      <ul className="space-y-2">
        {items.map((b: { id: string; customer_name: string; booking_date: string; start_time: string; seconds_until_start: number }) => (
          <li key={b.id}>
            <Link
              href={`/dashboard/bookings/${b.id}`}
              className="flex items-center justify-between gap-3 rounded-lg border border-brand-forest-800 bg-brand-forest-900 px-3 py-2 hover:border-brand-teal-400/40"
            >
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">{b.customer_name}</p>
                <p className="text-xs text-brand-teal-100/60">
                  {b.booking_date} · {b.start_time?.slice(0, 5)}
                </p>
              </div>
              <span className="shrink-0 text-xs font-bold text-brand-teal-300 tabular-nums">
                {formatCountdown(b.seconds_until_start)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
