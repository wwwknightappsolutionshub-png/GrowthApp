'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isLoyaltyAuthenticated, rewardsPath } from '@/lib/loyalty-portal-auth'

export function LoyaltyAuthGate({ tenant, children }: { tenant: string; children: React.ReactNode }) {
  const router = useRouter()

  useEffect(() => {
    if (!isLoyaltyAuthenticated(tenant)) {
      router.replace(rewardsPath(tenant, 'login'))
    }
  }, [tenant, router])

  if (!isLoyaltyAuthenticated(tenant)) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-sm text-slate-500">
        Checking sign-in…
      </div>
    )
  }

  return <>{children}</>
}
