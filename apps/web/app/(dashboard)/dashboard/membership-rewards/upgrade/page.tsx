'use client'

import Link from 'next/link'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle2, Gift, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'

const FEATURES = [
  'Tenant-level membership plans (parallel to salon industry memberships)',
  'Points ledger separate from referral cash payouts',
  'Bronze → Platinum loyalty tiers',
  'Rewards catalog and redemptions',
  'Public page at /p/your-business/memberships',
  'Auto points on bookings, invoices, reviews, and referrals',
]

export default function MembershipRewardsUpgradePage() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['membership-rewards-status'],
    queryFn: async () => (await membershipRewards.status()).data,
  })

  const checkout = useMutation({
    mutationFn: () =>
      membershipRewards.checkout({
        success_url: `${window.location.origin}/dashboard/membership-rewards?upgraded=1`,
        cancel_url: `${window.location.origin}/dashboard/membership-rewards/upgrade`,
      }),
    onSuccess: (res) => {
      const url = res.data?.checkout_url
      if (url) window.location.href = url
      else toast.error('Checkout is not configured yet. Contact support.')
    },
    onError: () => toast.error('Could not start checkout'),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  if (status?.has_membership_rewards) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-4 py-16 px-6">
        <CheckCircle2 className="w-12 h-12 mx-auto text-green-400" />
        <h1 className="text-2xl font-bold text-white">Membership &amp; Rewards is active</h1>
        <p className="text-brand-teal-100/70 text-sm">
          {status.trial_ends_at
            ? `Trial ends ${new Date(status.trial_ends_at).toLocaleDateString('en-GB')}.`
            : 'You have full access to plans, points, and your public landing page.'}
        </p>
        <Link
          href="/dashboard/membership-rewards"
          className="inline-flex text-brand-teal-300 hover:text-white font-semibold"
        >
          Open dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-6 px-6">
      <Link
        href="/dashboard/membership-rewards"
        className="inline-flex items-center gap-1 text-sm text-brand-teal-200 hover:text-white"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <div className="rounded-2xl border border-brand-forest-800 bg-gradient-to-br from-brand-forest-950 via-brand-forest-900 to-brand-forest-950 p-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-teal-600 text-white">
            <Gift className="w-6 h-6" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-teal-100/70">Add-on</p>
            <h1 className="text-2xl font-bold text-white">Membership &amp; Rewards</h1>
          </div>
        </div>
        <p className="text-sm text-brand-teal-100/75 mb-6">
          Run a cross-niche membership engine with loyalty points. Referral cash stays in the Referrals module — points
          are tracked separately.
        </p>
        <ul className="space-y-2 mb-8">
          {FEATURES.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-brand-teal-50">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-brand-teal-400 mt-0.5" />
              {f}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => checkout.mutate()}
          disabled={checkout.isPending || status?.stripe_configured === false}
          className="w-full rounded-lg bg-brand-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
        >
          {checkout.isPending ? 'Redirecting…' : 'Subscribe via Stripe'}
        </button>
        {status?.stripe_configured === false && (
          <p className="mt-3 text-xs text-center text-amber-200/90">
            Stripe billing for this add-on is not configured yet. Contact support or use your trial.
          </p>
        )}
        <p className="mt-3 text-xs text-center text-brand-teal-100/50">
          New tenants get a 7-day trial automatically on signup
        </p>
      </div>
    </div>
  )
}
