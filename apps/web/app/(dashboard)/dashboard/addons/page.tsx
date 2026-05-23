'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'

import { IndustryAddonsUpgradeAlert } from '@/components/addons/IndustryAddonsUpgradeAlert'
import { industryAddons } from '@/lib/api-client'

const CARDS = [
  {
    key: 'industry_booking' as const,
    title: 'Industry Booking',
    href: '/dashboard/addons/booking',
    flag: 'industry_booking' as const,
    desc: 'Enhanced scheduling for salon, realtor, or garage workflows.',
  },
  {
    key: 'industry_billing' as const,
    title: 'Industry Billing',
    href: '/dashboard/addons/billing',
    flag: 'industry_billing' as const,
    desc: 'Vertical-specific invoicing, tips, commissions, parts, and packages.',
  },
  {
    key: 'industry_crm' as const,
    title: 'Industry CRM',
    href: '/dashboard/addons/crm',
    flag: 'industry_crm' as const,
    desc: 'Rich customer and job history tailored to your industry.',
  },
]

export default function IndustryAddonsHubPage() {
  const q = useQuery({
    queryKey: ['addons', 'status'],
    queryFn: async () => (await industryAddons.status()).data,
  })
  const vertical = q.data?.vertical ?? 'salon'

  return (
    <div className="space-y-8 p-6">
      <IndustryAddonsUpgradeAlert />
      <div>
        <h1 className="text-2xl font-semibold text-white">Industry add-ons</h1>
        <p className="mt-1 text-sm text-slate-400">
          Premium tools for your vertical: <span className="capitalize text-brand-teal-200">{vertical}</span>
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {CARDS.map((card) => {
          const active = q.data?.[card.flag] ?? false
          return (
            <div
              key={card.key}
              className="rounded-xl border border-white/10 bg-white/5 p-5 flex flex-col"
            >
              <div className="flex items-center justify-between gap-2">
                <h2 className="font-semibold text-white">{card.title}</h2>
                <span
                  className={
                    active
                      ? 'rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-200'
                      : 'rounded-full bg-slate-500/20 px-2 py-0.5 text-xs text-slate-300'
                  }
                >
                  {active ? 'Active' : 'Locked'}
                </span>
              </div>
              <p className="mt-2 flex-1 text-sm text-slate-400">{card.desc}</p>
              <Link
                href={card.href}
                className="mt-4 text-sm font-medium text-brand-teal-300 hover:text-brand-teal-200"
              >
                {active ? 'Open module →' : 'Learn more →'}
              </Link>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-slate-500">
        Stripe checkout for industry add-ons ships in Phase 2. Contact support for early access grants.
      </p>
    </div>
  )
}
