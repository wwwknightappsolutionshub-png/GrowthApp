'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'

import { industryAddons } from '@/lib/api-client'

export function IndustryAddonsUpgradeAlert() {
  const { data } = useQuery({
    queryKey: ['addons', 'status'],
    queryFn: async () => (await industryAddons.status()).data,
  })

  if (!data) return null
  const hasAny = data.industry_booking || data.industry_billing || data.industry_crm
  if (hasAny) return null

  return (
    <div className="flex items-start gap-3 rounded-xl border border-brand-teal-500/40 bg-brand-teal-600/10 p-4">
      <Sparkles className="w-5 h-5 text-brand-teal-300 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white">Unlock industry add-ons</p>
        <p className="text-xs text-brand-teal-100/75 mt-1">
          Premium booking, billing, and CRM tools for salon or garage workflows are not active on your plan.
          Upgrade to use add-on features.
        </p>
        <Link
          href="/dashboard/addons"
          className="mt-2 inline-flex text-xs font-semibold text-brand-teal-300 hover:underline"
        >
          View add-ons & upgrade →
        </Link>
      </div>
    </div>
  )
}
