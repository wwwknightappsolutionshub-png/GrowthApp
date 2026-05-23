'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Gift } from 'lucide-react'
import { publicBooking } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { PUBLIC_FIELD_CLASS, PUBLIC_LABEL_CLASS } from '@/lib/public-booking-ui'
import { toast } from 'sonner'

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

  const accent = widget?.widget_primary_color || '#5b21b6'
  const name = widget?.tenant_name || 'Our business'

  return (
    <PublicBookShell variant="refer" tenantName={name} subtitle="Refer a friend and earn rewards" accent={accent}>
      {done ? (
        <div className="text-center space-y-3 py-4">
          <Gift className="w-12 h-12 mx-auto text-violet-700" />
          <h2 className="text-xl font-bold text-slate-900">Thank you!</h2>
          <p className="text-sm text-slate-600">
            Your referral has been added to our pipeline. Loyalty points may apply if the business uses Membership & Rewards.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-violet-900/90 bg-violet-50 border border-violet-200 rounded-lg px-3 py-2 mb-2">
            Tell us about your referral — we&apos;ll add them to our pipeline as a new lead.
          </p>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault()
              submit.mutate()
            }}
          >
            <div>
              <label className={PUBLIC_LABEL_CLASS}>Your name *</label>
              <input
                className={PUBLIC_FIELD_CLASS}
                required
                value={form.referral_name}
                onChange={(e) => setForm((f) => ({ ...f, referral_name: e.target.value }))}
              />
            </div>
            <div>
              <label className={PUBLIC_LABEL_CLASS}>Your phone *</label>
              <input
                className={PUBLIC_FIELD_CLASS}
                type="tel"
                required
                value={form.referral_phone}
                onChange={(e) => setForm((f) => ({ ...f, referral_phone: e.target.value }))}
              />
            </div>
            <div>
              <label className={PUBLIC_LABEL_CLASS}>Friend&apos;s phone *</label>
              <input
                className={PUBLIC_FIELD_CLASS}
                type="tel"
                required
                value={form.referred_phone}
                onChange={(e) => setForm((f) => ({ ...f, referred_phone: e.target.value }))}
              />
            </div>
            <div>
              <label className={PUBLIC_LABEL_CLASS}>Friend&apos;s email</label>
              <input
                className={PUBLIC_FIELD_CLASS}
                type="email"
                value={form.referred_email}
                onChange={(e) => setForm((f) => ({ ...f, referred_email: e.target.value }))}
              />
            </div>
            <div>
              <label className={PUBLIC_LABEL_CLASS}>Why are you referring them? *</label>
              <textarea
                className={PUBLIC_FIELD_CLASS}
                rows={4}
                required
                value={form.referral_reason}
                onChange={(e) => setForm((f) => ({ ...f, referral_reason: e.target.value }))}
              />
            </div>
            <button
              type="submit"
              disabled={submit.isPending}
              className="w-full py-3.5 rounded-xl text-white font-semibold text-sm disabled:opacity-50 shadow-md"
              style={{ backgroundColor: accent }}
            >
              {submit.isPending ? 'Sending…' : 'Submit referral'}
            </button>
          </form>
        </>
      )}
    </PublicBookShell>
  )
}
