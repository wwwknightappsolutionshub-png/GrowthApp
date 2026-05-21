'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { bookingSettingsSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { useState, useEffect } from 'react'

export default function BookingSettingsPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['bookings', 'settings'],
    queryFn: () => bookings.getSettings().then((r) => r.data),
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

  useEffect(() => {
    if (data) setForm((f) => ({ ...f, ...data }))
  }, [data])

  const saveMutation = useMutation({
    mutationFn: () => {
      const parsed = bookingSettingsSchema.parse({
        ...form,
        default_deposit_pence: Number(form.default_deposit_pence),
        no_show_fee_pence: Number(form.no_show_fee_pence),
        service_fee_percent: Number(form.service_fee_percent),
        default_duration_minutes: Number(form.default_duration_minutes),
        min_notice_hours: Number(form.min_notice_hours),
      })
      return bookings.updateSettings(parsed).then((r) => r.data)
    },
    onSuccess: () => {
      toast.success('Settings saved')
      qc.invalidateQueries({ queryKey: ['bookings', 'settings'] })
    },
    onError: () => toast.error('Failed to save'),
  })

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading…</div>
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">← Bookings</Link>
        <h1 className="text-2xl font-bold text-foreground">Booking settings</h1>
      </div>
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
        <label className="block text-sm text-brand-teal-100/80">Timezone</label>
        <input className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" value={form.timezone} onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))} />
        <label className="flex items-center gap-2 text-sm text-white">
          <input type="checkbox" checked={form.deposit_enabled} onChange={(e) => setForm((f) => ({ ...f, deposit_enabled: e.target.checked }))} />
          Require deposit
        </label>
        <input type="number" className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="Default deposit (pence)" value={form.default_deposit_pence} onChange={(e) => setForm((f) => ({ ...f, default_deposit_pence: Number(e.target.value) }))} />
        <input type="number" className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="No-show fee (pence)" value={form.no_show_fee_pence} onChange={(e) => setForm((f) => ({ ...f, no_show_fee_pence: Number(e.target.value) }))} />
        <input className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="Widget colour" value={form.widget_primary_color} onChange={(e) => setForm((f) => ({ ...f, widget_primary_color: e.target.value }))} />
        <input className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="Google Pixel ID" value={form.google_pixel_id || ''} onChange={(e) => setForm((f) => ({ ...f, google_pixel_id: e.target.value }))} />
        <input className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="Meta Pixel ID" value={form.meta_pixel_id || ''} onChange={(e) => setForm((f) => ({ ...f, meta_pixel_id: e.target.value }))} />
        <button type="button" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending} className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-medium">
          Save settings
        </button>
      </div>
    </div>
  )
}
