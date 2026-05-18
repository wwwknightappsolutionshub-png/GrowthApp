'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { auth, referrals } from '@/lib/api-client'

export default function ClientReferralRewardsPage() {
  const { data: me } = useQuery({ queryKey: ['me'], queryFn: () => auth.me().then((r) => r.data) })
  const userId = me?.id as string | undefined
  const { data: dash } = useQuery({
    queryKey: ['referral-dash', userId],
    enabled: !!userId,
    queryFn: () => referrals.dashboard(userId!).then((r) => r.data),
  })

  return (
    <div className="mx-auto max-w-xl space-y-6 px-4 py-8">
      <h1 className="font-display text-2xl font-bold">Your referral rewards</h1>
      <p className="text-sm text-muted-foreground">
        Status for referrals you have made.{' '}
        <Link href="/dashboard/referrals" className="text-brand-forest-700 underline">
          Open full referral hub
        </Link>
      </p>
      <ul className="space-y-2 text-sm">
        {(dash?.events || []).map((ev: any) => (
          <li key={ev.id} className="rounded-md border border-border bg-card px-3 py-2">
            <span className="font-medium">{ev.status}</span>
            <span className="text-muted-foreground"> · reward {ev.reward_status}</span>
            <span className="text-muted-foreground"> · £{Number(ev.reward_amount).toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
