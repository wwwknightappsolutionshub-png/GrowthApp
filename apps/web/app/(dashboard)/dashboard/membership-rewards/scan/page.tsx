'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

import { LoyaltyScanSection } from '@/components/membership-rewards/LoyaltyScanSection'
import { MembershipRewardsGate } from '@/components/membership-rewards/MembershipRewardsGate'

export default function MembershipRewardsScanPage() {
  return (
    <MembershipRewardsGate>
      <div className="space-y-6 p-6">
        <Link
          href="/dashboard/membership-rewards"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Membership &amp; Rewards
        </Link>
        <LoyaltyScanSection />
      </div>
    </MembershipRewardsGate>
  )
}
