'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Gift } from 'lucide-react'
import { publicBooking } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { toast } from 'sonner'

const fieldClass =
  'w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-emerald-600/30 focus:border-emerald-700'

export default function PublicReferPage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()
  const [form, setForm] = useState({
    referral_name: '',
    referral_phone: '',
    referred_phone: '',
    referred_email: '',
    referral_reason: '',
  })
  const [done, setDone] = useState(false)

  const { data: widget } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: () => publicBooking.widget(slug).then((r) => r.data),
    enabled: !!slug,
  })

  const submit = useMutation({
    mutationFn: () => publicBooking.submitRefer(slug, form).then((r) => r.data),
    onSuccess: () => {
      setDone(true)
      toast.success('Referral submitted — thank you!')
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not submit referral'),
  })

  const accent = widget?.widget_primary_color || '#166534'
  const name = widget?.tenant_name || 'Our business'

  return (
    <PublicBookShell tenantName={name} subtitle="Refer & Win" accent={accent}>
      {done ? (
        <div className="text-center space-y-3 py-4">
          <Gift className="w-12 h-12 mx-auto text-emerald-700" />
          <h2 className="text-xl font-bold text-slate-900">Thank you!</h2>
          <p className="text-sm text-slate-600">
            Your referral has been added to our pipeline. Rewards apply per active referral program rules.
          </p>
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            submit.mutate()
          }}
        >
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Your name *</label>
            <input
              className={fieldClass}
              required
              value={form.referral_name}
              onChange={(e) => setForm((f) => ({ ...f, referral_name: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Your phone *</label>
            <input
              className={fieldClass}
              type="tel"
              required
              value={form.referral_phone}
              onChange={(e) => setForm((f) => ({ ...f, referral_phone: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Friend&apos;s phone *</label>
            <input
              className={fieldClass}
              type="tel"
              required
              value={form.referred_phone}
              onChange={(e) => setForm((f) => ({ ...f, referred_phone: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Friend&apos;s email</label>
            <input
              className={fieldClass}
              type="email"
              value={form.referred_email}
              onChange={(e) => setForm((f) => ({ ...f, referred_email: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Why are you referring them? *</label>
            <textarea
              className={fieldClass}
              rows={4}
              required
              value={form.referral_reason}
              onChange={(e) => setForm((f) => ({ ...f, referral_reason: e.target.value }))}
            />
          </div>
          <button
            type="submit"
            disabled={submit.isPending}
            className="w-full py-3.5 rounded-xl text-white font-semibold text-sm disabled:opacity-50"
            style={{ backgroundColor: accent }}
          >
            {submit.isPending ? 'Sending…' : 'Submit referral'}
          </button>
        </form>
      )}
    </PublicBookShell>
  )
}
