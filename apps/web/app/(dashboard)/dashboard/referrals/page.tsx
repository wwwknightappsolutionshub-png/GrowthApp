'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { auth, referrals } from '@/lib/api-client'
import { toast } from 'sonner'

export default function ReferralsPage() {
  const qc = useQueryClient()
  const { data: me } = useQuery({ queryKey: ['me'], queryFn: () => auth.me().then((r) => r.data) })
  const userId = me?.id as string | undefined

  const [rewardAmount, setRewardAmount] = useState('25')
  const [rewardType, setRewardType] = useState('fixed_amount')
  const [delivery, setDelivery] = useState('payout')
  const [programId, setProgramId] = useState('')

  const createProgram = useMutation({
    mutationFn: () =>
      referrals.createProgram({
        type: 'tradesman',
        reward_amount: parseFloat(rewardAmount || '0'),
        reward_type: rewardType,
        reward_delivery_method: delivery,
        rules: {
          reward_conditions: {
            reward_after_signup: true,
            reward_after_job_completed: true,
            reward_after_invoice_paid: true,
          },
          auto_send_referral_invite_after_job_completion: false,
          auto_send_only_to_4_5_star_clients: false,
          send_frequency_limit: 0,
        },
      }),
    onSuccess: (res) => {
      setProgramId(res.data.id)
      toast.success('Program saved (disabled until approved).')
      qc.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Could not create program'),
  })

  const submit = useMutation({
    mutationFn: () => referrals.submitProgram(programId),
    onSuccess: () => toast.success('Submitted for approval'),
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Submit failed'),
  })

  const genLink = useMutation({
    mutationFn: () => referrals.generateLink({ program_id: programId }),
    onSuccess: () => {
      toast.success('Link generated')
      if (userId) qc.invalidateQueries({ queryKey: ['referral-links', userId] })
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Link generation failed'),
  })

  const { data: links } = useQuery({
    queryKey: ['referral-links', userId],
    enabled: !!userId,
    queryFn: () => referrals.listLinks(userId!).then((r) => r.data),
  })

  const { data: dash } = useQuery({
    queryKey: ['referral-dash', userId],
    enabled: !!userId,
    queryFn: () => referrals.dashboard(userId!).then((r) => r.data),
  })

  const primaryLink = links?.[0]

  return (
    <div className="mx-auto max-w-3xl space-y-10 px-4 py-8">
      <div>
        <h1 className="font-display text-2xl font-bold">Referrals</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Tradesman referral program settings, your link and QR code, and reward tracking.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Reward rules</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-xs font-medium text-muted-foreground">
            Reward amount
            <input
              className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={rewardAmount}
              onChange={(e) => setRewardAmount(e.target.value)}
            />
          </label>
          <label className="text-xs font-medium text-muted-foreground">
            Reward type
            <select
              className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={rewardType}
              onChange={(e) => setRewardType(e.target.value)}
            >
              <option value="fixed_amount">fixed_amount</option>
              <option value="percentage">percentage</option>
              <option value="credit">credit</option>
              <option value="gift_card">gift_card</option>
            </select>
          </label>
          <label className="text-xs font-medium text-muted-foreground sm:col-span-2">
            Reward delivery
            <select
              className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={delivery}
              onChange={(e) => setDelivery(e.target.value)}
            >
              <option value="payout">payout</option>
              <option value="invoice_credit">invoice_credit</option>
              <option value="coupon_code">coupon_code</option>
              <option value="gift_card">gift_card</option>
            </select>
          </label>
        </div>
        <button
          type="button"
          className="mt-4 rounded-md bg-brand-forest-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-forest-700"
          onClick={() => createProgram.mutate()}
          disabled={createProgram.isPending}
        >
          Save program (tenant)
        </button>
        {programId && (
          <p className="mt-2 font-mono text-xs text-muted-foreground">Program ID: {programId}</p>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Approval</h2>
        <button
          type="button"
          className="mt-3 rounded-md border border-input px-4 py-2 text-sm"
          disabled={!programId || submit.isPending}
          onClick={() => submit.mutate()}
        >
          Submit for SuperAdmin approval
        </button>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Referral link & QR</h2>
        <button
          type="button"
          className="mt-3 rounded-md bg-brand-teal-600 px-4 py-2 text-sm font-medium text-white"
          disabled={!programId || genLink.isPending}
          onClick={() => genLink.mutate()}
        >
          Generate my link
        </button>
        {primaryLink && (
          <div className="mt-4 space-y-2 text-sm">
            <p>
              <span className="text-muted-foreground">Link:</span>{' '}
              <a className="text-brand-forest-700 underline" href={primaryLink.ref_link}>
                {primaryLink.ref_link}
              </a>
            </p>
            <p className="text-muted-foreground">Code: {primaryLink.ref_code}</p>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={primaryLink.qr_code_url} alt="Referral QR" className="mt-2 h-40 w-40 rounded border border-border" />
          </div>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Analytics</h2>
        {dash && (
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-muted-foreground">Clicks</dt>
              <dd className="text-lg font-semibold">{dash.clicks}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Signups</dt>
              <dd className="text-lg font-semibold">{dash.signups}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Paid users</dt>
              <dd className="text-lg font-semibold">{dash.paid_users}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Commission</dt>
              <dd className="text-lg font-semibold">£{Number(dash.commission_earned).toFixed(2)}</dd>
            </div>
          </dl>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Reward tracking</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="py-2 pr-2">Event</th>
                <th className="py-2 pr-2">Status</th>
                <th className="py-2 pr-2">Reward</th>
                <th className="py-2">Amount</th>
              </tr>
            </thead>
            <tbody>
              {(dash?.events || []).map((ev: any) => (
                <tr key={ev.id} className="border-b border-border/60">
                  <td className="py-2 pr-2 font-mono">{ev.id.slice(0, 8)}…</td>
                  <td className="py-2 pr-2">{ev.status}</td>
                  <td className="py-2 pr-2">{ev.reward_status}</td>
                  <td className="py-2">{ev.reward_amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
