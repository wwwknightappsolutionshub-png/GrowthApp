import { redirect } from 'next/navigation'
import { rewardsPath } from '@/lib/loyalty-portal-auth'

export default function RewardsTenantHome({ params }: { params: { tenant: string } }) {
  redirect(rewardsPath(params.tenant, 'login'))
}
