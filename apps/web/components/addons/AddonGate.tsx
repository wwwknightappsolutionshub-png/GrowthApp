'use client'

import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { AddonUpgradeScreen } from '@/components/addons/AddonUpgradeScreen'
import { industryAddons, type AddonStatusResponse } from '@/lib/api-client'

type Feature = 'industry_booking' | 'industry_billing' | 'industry_crm'

function isEntitled(status: AddonStatusResponse | undefined, feature: Feature): boolean {
  if (!status) return false
  if (feature === 'industry_booking') return status.industry_booking
  if (feature === 'industry_billing') return status.industry_billing
  return status.industry_crm
}

export function AddonGate({
  feature,
  children,
}: {
  feature: Feature
  children: ReactNode
}) {
  const q = useQuery({
    queryKey: ['addons', 'status'],
    queryFn: async () => (await industryAddons.status()).data,
  })
  if (q.isLoading) {
    return <p className="text-sm text-slate-400">Loading…</p>
  }
  if (!isEntitled(q.data, feature)) {
    return <AddonUpgradeScreen feature={feature} />
  }
  return <>{children}</>
}
