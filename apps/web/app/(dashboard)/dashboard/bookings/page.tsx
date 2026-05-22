'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  Bell,
  Calendar,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Filter,
  LayoutGrid,
  Users,
} from 'lucide-react'
import { bookings, auth, tenants } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'
import { ModuleMetricCharts, type MetricSeries } from '@/components/modules/ModuleMetricCharts'
import { ModuleCardGrid, type ModuleCardItem } from '@/components/modules/ModuleCardGrid'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { UpcomingCountdown } from '@/components/bookings/UpcomingCountdown'

type BookingRow = {
  id: string
  customer_name: string
  booking_date: string
  start_time: string
  status: string
}

export default function BookingsHubPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [calMonth, setCalMonth] = useState(() => new Date())

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })
  const { data: analytics } = useQuery({
    queryKey: ['bookings', 'analytics', 30],
    queryFn: () => bookings.getAnalytics({ days: 30 }).then((r) => r.data),
  })
  const { data: listData } = useQuery({
    queryKey: ['bookings', 'hub-list'],
    queryFn: () => bookings.list({ page: 1, page_size: 200 }).then((r) => r.data),
  })

  const items: BookingRow[] = listData?.items ?? []
  const today = new Date().toISOString().slice(0, 10)

  const upcoming = items.filter(
    (b) => ['confirmed', 'pending'].includes(b.status) && b.booking_date >= today
  ).length
  const completed = items.filter((b) => b.status === 'completed').length
  const missed = items.filter((b) => ['no_show', 'cancelled'].includes(b.status)).length
  const bookedSessions = analytics?.total_bookings ?? items.length

  const chartData: MetricSeries[] = [
    { name: 'This week', booked: bookedSessions, upcoming, completed, missed },
    {
      name: 'Rates',
      booked: analytics?.confirmed ?? 0,
      upcoming: Math.round(analytics?.utilization_rate ?? 0),
      completed: analytics?.completed ?? 0,
      missed: analytics?.no_show ?? 0,
    },
  ]

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return items
    return items.filter((b) => b.status === statusFilter)
  }, [items, statusFilter])

  const gridCards: ModuleCardItem[] = [
    {
      title: 'Booking widget',
      description: 'Embed the public booking form on your site or landing page.',
      href: '/dashboard/bookings/widget',
      icon: LayoutGrid,
    },
    {
      title: 'Staff',
      description: 'Manage team members, shifts, and availability.',
      href: '/dashboard/bookings/staff',
      icon: Users,
    },
    {
      title: 'Analytics',
      description: 'Deep dive into utilisation, channels, and revenue.',
      href: '/dashboard/bookings/analytics',
      icon: BarChart3,
    },
    {
      title: 'Booking reminders',
      description: 'Client SMS/email reminders, schedule, and upcoming sessions.',
      href: '/dashboard/bookings/settings',
      icon: Bell,
      badge: 'Settings',
    },
    {
      title: 'Reports',
      description: 'Export booking performance and filter by date range.',
      href: '/dashboard/bookings/analytics',
      icon: Filter,
    },
  ]

  const year = calMonth.getFullYear()
  const month = calMonth.getMonth()
  const firstDay = new Date(year, month, 1)
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const startPad = firstDay.getDay()
  const bookingsByDate = useMemo(() => {
    const m: Record<string, BookingRow[]> = {}
    for (const b of items) {
      const d = b.booking_date?.slice(0, 10)
      if (!d) continue
      m[d] = m[d] ?? []
      m[d].push(b)
    }
    return m
  }, [items])

  return (
    <div className="space-y-6">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Bookings — sessions, staff, reminders, and calendar"
      />

      <ModuleMetricCharts
        title="Booking analytics"
        subtitle="Booked sessions, upcoming, completed, and missed"
        data={chartData}
        seriesKeys={['booked', 'upcoming', 'completed', 'missed']}
      />

      <ModuleCardGrid items={gridCards} />

      <UpcomingCountdown />

      <div className="flex justify-end">
        <Link
          href="/dashboard/bookings/new"
          className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold hover:bg-brand-forest-600"
        >
          + New booking
        </Link>
      </div>

      <section className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-brand-teal-300" />
            Calendar & availability
          </h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCalMonth(new Date(year, month - 1, 1))}
              className="p-2 rounded-lg border border-brand-forest-700 text-brand-teal-100/80 hover:bg-brand-forest-900"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-semibold text-white min-w-[140px] text-center">
              {calMonth.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}
            </span>
            <button
              type="button"
              onClick={() => setCalMonth(new Date(year, month + 1, 1))}
              className="p-2 rounded-lg border border-brand-forest-700 text-brand-teal-100/80 hover:bg-brand-forest-900"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-bold uppercase text-brand-teal-100/50 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d}>{d}</div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: startPad }).map((_, i) => (
            <div key={`pad-${i}`} className="min-h-[72px]" />
          ))}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            const dayBookings = bookingsByDate[key] ?? []
            return (
              <div
                key={key}
                className={`min-h-[72px] rounded-lg border p-1 text-left ${
                  dayBookings.length
                    ? 'border-brand-teal-400/40 bg-brand-forest-900'
                    : 'border-brand-forest-800 bg-brand-forest-950/50'
                }`}
              >
                <span className="text-xs font-semibold text-white">{day}</span>
                {dayBookings.slice(0, 2).map((b) => (
                  <p key={b.id} className="text-[9px] text-brand-teal-100/70 truncate mt-0.5">
                    {b.start_time?.slice(0, 5)} {b.customer_name}
                  </p>
                ))}
                {dayBookings.length > 2 ? (
                  <p className="text-[9px] text-brand-teal-300">+{dayBookings.length - 2}</p>
                ) : null}
              </div>
            )
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-brand-forest-800">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            All bookings
          </h2>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-brand-forest-700 bg-brand-forest-900 px-3 py-1.5 text-sm text-white"
          >
            <option value="all">All statuses</option>
            <option value="confirmed">Confirmed</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="no_show">No show</option>
          </select>
        </div>
        <ul className="divide-y divide-brand-forest-800 max-h-[420px] overflow-y-auto">
          {filtered.length === 0 ? (
            <li className="px-5 py-12 text-center text-sm text-brand-teal-100/60">No bookings match this filter.</li>
          ) : (
            filtered.map((b) => (
              <li key={b.id} className="px-5 py-3 flex justify-between gap-4 hover:bg-brand-forest-900">
                <Link href={`/dashboard/bookings/${b.id}`} className="min-w-0 flex-1">
                  <p className="font-semibold text-white text-sm">{b.customer_name}</p>
                  <p className="text-xs text-brand-teal-100/65 mt-0.5">
                    {formatDate(b.booking_date)} · {b.start_time?.slice(0, 5)}
                  </p>
                </Link>
                <span className="text-xs capitalize px-2 py-0.5 rounded-full bg-brand-forest-800 text-brand-teal-200 h-fit">
                  {b.status}
                </span>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  )
}
