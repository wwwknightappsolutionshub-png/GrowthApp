'use client'

import { MembershipRewardsDashboard } from '@/components/membership-rewards/MembershipRewardsDashboard'
import { MembershipRewardsGate } from '@/components/membership-rewards/MembershipRewardsGate'

export default function MembershipRewardsPage() {
  return (
    <MembershipRewardsGate>
      <MembershipRewardsDashboard />
    </MembershipRewardsGate>
  )
}
