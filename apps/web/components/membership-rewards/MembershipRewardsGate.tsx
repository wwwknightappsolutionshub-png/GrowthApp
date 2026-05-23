'use client'

import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Gift, Loader2 } from 'lucide-react'

import { membershipRewards } from '@/lib/api-client'

export function MembershipRewardsGate({ children }: { children: ReactNode }) {
  const q = useQuery({
    queryKey: ['membership-rewards-status'],
    queryFn: async () => (await membershipRewards.status()).data,
  })

  if (q.isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  if (!q.data?.has_membership_rewards) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-4 py-16 px-6">
        <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-teal-600/20 text-brand-teal-300">
          <Gift className="w-7 h-7" />
        </span>
        <h1 className="text-2xl font-bold text-white">Membership &amp; Rewards</h1>
        <p className="text-sm text-brand-teal-100/70">
          Your 7-day trial has ended. Upgrade to manage membership plans, loyalty points, and your public
          memberships page.
        </p>
        <Link
          href="/dashboard/membership-rewards/upgrade"
          className="inline-flex rounded-lg bg-brand-teal-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-teal-500"
        >
          Upgrade now
        </Link>
      </div>
    )
  }

  return <>{children}</>
}
