'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { bookingSettingsSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { useState, useEffect, useMemo } from 'react'
import { Bell, Calendar, Mail, MessageSquare } from 'lucide-react'
import { formatDate } from '@/lib/utils'

type ReminderConfig = {
  email?: number[]
  sms?: number[]
}

type BookingRow = {
  id: string
  customer_name: string
  customer_email?: string | null
  customer_phone?: string | null
  booking_date: string
  start_time: string
  status: string
}

const DEFAULT_REMINDERS: ReminderConfig = { email: [48, 24], sms: [24] }

export default function BookingSettingsPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['bookings', 'settings'],
    queryFn: () => bookings.getSettings().then((r) => r.data),
  })

  const { data: listData } = useQuery({
    queryKey: ['bookings', 'reminder-upcoming'],
    queryFn: () => bookings.list({ page: 1, page_size: 100 }).then((r) => r.data),
  })

  const [form, setForm] = useState({
    timezone: 'Europe/London',
    default_duration_minutes: 60,
    deposit_enabled: false,
    default_deposit_pence: 0,
    no_show_fee_pence: 0,
    service_fee_percent: 0,
    allow_self_reschedule: true,
    allow_self_cancel: true,
    min_notice_hours: 24,
    google_pixel_id: '',
    meta_pixel_id: '',
    widget_primary_color: '#166534',
  })
  const [emailHours, setEmailHours] = useState('48, 24')
  const [smsHours, setSmsHours] = useState('24')

  useEffect(() => {
    if (!data) return
    setForm((f) => ({ ...f, ...data }))
    const cfg = (data.automation_config as { reminders?: ReminderConfig })?.reminders ?? DEFAULT_REMINDERS
    setEmailHours((cfg.email ?? DEFAULT_REMINDERS.email ?? []).join(', '))
    setSmsHours((cfg.sms ?? DEFAULT_REMINDERS.sms ?? []).join(', '))
  }, [data])

  const saveMutation = useMutation({
    mutationFn: () => {
      const parseHours = (raw: string) =>
        raw
          .split(',')
          .map((s) => parseInt(s.trim(), 10))
          .filter((n) => !Number.isNaN(n) && n > 0)

      const automation_config = {
        ...(data?.automation_config as object),
        reminders: {
          email: parseHours(emailHours),
          sms: parseHours(smsHours),
        },
      }

      const parsed = bookingSettingsSchema.parse({
        ...form,
        default_deposit_pence: Number(form.default_deposit_pence),
        no_show_fee_pence: Number(form.no_show_fee_pence),
        service_fee_percent: Number(form.service_fee_percent),
        default_duration_minutes: Number(form.default_duration_minutes),
        min_notice_hours: Number(form.min_notice_hours),
      })
      return bookings
        .updateSettings({ ...parsed, automation_config })
        .then((r) => r.data)
    },
    onSuccess: () => {
      toast.success('Reminder settings saved')
      qc.invalidateQueries({ queryKey: ['bookings', 'settings'] })
    },
    onError: () => toast.error('Failed to save'),
  })

  const sendReminder = useMutation({
    mutationFn: ({ id, channel }: { id: string; channel: 'email' | 'sms' }) =>
      bookings.sendClientReminder(id, channel),
    onSuccess: () => toast.success('Reminder sent to customer'),
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const d = err.response?.data?.detail
      toast.error(typeof d === 'string' ? d : 'Could not send reminder')
    },
  })

  const today = new Date().toISOString().slice(0, 10)
  const upcoming = useMemo(() => {
    const items: BookingRow[] = listData?.items ?? []
    return items
      .filter((b) => ['confirmed', 'pending'].includes(b.status) && b.booking_date >= today)
      .sort((a, b) => a.booking_date.localeCompare(b.booking_date))
      .slice(0, 20)
  }, [listData, today])

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading…</div>
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex flex-wrap items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
          ← Bookings
        </Link>
        <Link href="/dashboard/bookings/widget" className="text-sm text-brand-teal-300 hover:text-white">
          Widget & QR codes
        </Link>
        <Link href="/dashboard/bookings/form-builder" className="text-sm text-brand-teal-300 hover:text-white">
          Form builder
        </Link>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 w-full sm:w-auto">
          <Bell className="w-6 h-6 text-brand-teal-300" />
          Client reminder management
        </h1>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
        <h2 className="font-semibold text-white">Automated client reminders</h2>
        <p className="text-sm text-brand-teal-100/65">
          SMS and email go to your customer only — hours before their appointment.
        </p>
        <label className="block text-sm text-brand-teal-100/80 flex items-center gap-2">
          <Mail className="w-4 h-4" />
          Email hours before (comma-separated)
        </label>
        <input
          className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
          value={emailHours}
          onChange={(e) => setEmailHours(e.target.value)}
          placeholder="48, 24"
        />
        <label className="block text-sm text-brand-teal-100/80 flex items-center gap-2">
          <MessageSquare className="w-4 h-4" />
          SMS hours before (comma-separated)
        </label>
        <input
          className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
          value={smsHours}
          onChange={(e) => setSmsHours(e.target.value)}
          placeholder="24"
        />
        <button
          type="button"
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold"
        >
          Save reminder schedule
        </button>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 overflow-hidden">
        <div className="px-5 py-4 border-b border-brand-forest-800 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-brand-teal-300" />
          <h2 className="text-sm font-bold text-white">Upcoming bookings — send now</h2>
        </div>
        <ul className="divide-y divide-brand-forest-800 max-h-[420px] overflow-y-auto">
          {upcoming.length === 0 ? (
            <li className="px-5 py-10 text-center text-sm text-brand-teal-100/60">No upcoming sessions.</li>
          ) : (
            upcoming.map((b) => (
              <li key={b.id} className="px-5 py-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-white text-sm">{b.customer_name}</p>
                  <p className="text-xs text-brand-teal-100/65 mt-0.5">
                    {formatDate(b.booking_date)} · {b.start_time?.slice(0, 5)} · {b.status}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={!b.customer_email || sendReminder.isPending}
                    onClick={() => sendReminder.mutate({ id: b.id, channel: 'email' })}
                    className="text-xs px-3 py-1.5 rounded-lg border border-brand-forest-700 text-white disabled:opacity-40"
                  >
                    Email
                  </button>
                  <button
                    type="button"
                    disabled={!b.customer_phone || sendReminder.isPending}
                    onClick={() => sendReminder.mutate({ id: b.id, channel: 'sms' })}
                    className="text-xs px-3 py-1.5 rounded-lg bg-brand-forest-700 text-white disabled:opacity-40"
                  >
                    SMS
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>

      <details className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-4">
        <summary className="text-sm font-semibold text-white cursor-pointer">Widget & deposit settings</summary>
        <div className="mt-4 space-y-3">
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            value={form.timezone}
            onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
          />
          <label className="flex items-center gap-2 text-sm text-white">
            <input
              type="checkbox"
              checked={form.deposit_enabled}
              onChange={(e) => setForm((f) => ({ ...f, deposit_enabled: e.target.checked }))}
            />
            Require deposit
          </label>
          <button
            type="button"
            onClick={() => saveMutation.mutate()}
            className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm"
          >
            Save all settings
          </button>
        </div>
      </details>
    </div>
  )
}
