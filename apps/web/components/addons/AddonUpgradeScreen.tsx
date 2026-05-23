'use client'

import Link from 'next/link'

const COPY: Record<string, { title: string; body: string }> = {
  industry_booking: {
    title: 'Industry Booking',
    body: 'Multi-service scheduling, resource allocation, and vertical-specific booking flows.',
  },
  industry_billing: {
    title: 'Industry Billing',
    body: 'Specialized invoicing: tips, commissions, parts markup, memberships, and more.',
  },
  industry_crm: {
    title: 'Industry CRM',
    body: 'Deep customer history: stylist notes, property showings, vehicle repair timelines.',
  },
}

export function AddonUpgradeScreen({
  feature,
}: {
  feature: 'industry_booking' | 'industry_billing' | 'industry_crm'
}) {
  const c = COPY[feature] ?? { title: 'Premium add-on', body: 'Upgrade to unlock this module.' }
  return (
    <div className="mx-auto max-w-lg rounded-2xl border border-white/10 bg-white/5 p-8 text-center">
      <p className="text-xs font-semibold uppercase tracking-wider text-brand-teal-300">Paid add-on</p>
      <h1 className="mt-2 text-2xl font-semibold text-white">{c.title}</h1>
      <p className="mt-3 text-sm text-slate-300">{c.body}</p>
      <Link
        href="/dashboard/addons"
        className="mt-6 inline-flex rounded-lg bg-brand-teal-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-teal-400"
      >
        View add-ons & upgrade
      </Link>
    </div>
  )
}
