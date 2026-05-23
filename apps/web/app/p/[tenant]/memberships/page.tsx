import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { MembershipInterestForm } from '@/components/membership-rewards/MembershipInterestForm'

type MembershipPlan = {
  id: string
  name: string
  description: string | null
  billing_cycle: string
  price_pence: number
  discount_percent: number
  included_services: string[]
}

type MembershipTier = {
  code: string
  name: string
  min_points_lifetime: number
  benefits: unknown[]
}

type MembershipPageJson = {
  tenant_slug: string
  tenant_name: string
  title: string
  meta_description: string | null
  hero: { headline?: string; subheadline?: string }
  benefits: { title?: string; body?: string }[]
  cta_label: string
  cta_href: string | null
  plans: MembershipPlan[]
  tiers: MembershipTier[]
}

async function fetchMemberships(tenant: string): Promise<MembershipPageJson | null> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return null
  const url = `${base}/api/v1/public/memberships/${encodeURIComponent(tenant)}`
  try {
    const res = await fetch(url, { next: { revalidate: 60 } })
    if (!res.ok) return null
    return (await res.json()) as MembershipPageJson
  } catch {
    return null
  }
}

function formatPrice(pence: number): string {
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(pence / 100)
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ tenant: string }>
}): Promise<Metadata> {
  const { tenant } = await params
  const page = await fetchMemberships(tenant)
  if (!page) return { title: 'Memberships' }
  return {
    title: page.title,
    description: page.meta_description || undefined,
    openGraph: {
      title: page.title,
      description: page.meta_description || undefined,
    },
  }
}

export default async function PublicMembershipsPage({
  params,
}: {
  params: Promise<{ tenant: string }>
}) {
  const { tenant } = await params
  const page = await fetchMemberships(tenant)
  if (!page) notFound()

  const headline = page.hero?.headline || page.title
  const subheadline = page.hero?.subheadline

  return (
    <main className="min-h-screen bg-white text-gray-900 antialiased">
      <section className="bg-gradient-to-br from-emerald-800 to-emerald-950 text-white px-6 py-20 text-center">
        <p className="text-sm uppercase tracking-widest text-emerald-200 mb-3">{page.tenant_name}</p>
        <h1 className="text-4xl md:text-5xl font-bold max-w-3xl mx-auto">{headline}</h1>
        {subheadline ? (
          <p className="mt-4 text-lg text-emerald-100 max-w-2xl mx-auto">{subheadline}</p>
        ) : null}
        {page.cta_href ? (
          <a
            href={page.cta_href}
            className="inline-block mt-8 rounded-lg bg-white text-emerald-900 font-semibold px-6 py-3 hover:bg-emerald-50"
          >
            {page.cta_label}
          </a>
        ) : null}
      </section>

      {page.benefits.length > 0 ? (
        <section className="max-w-5xl mx-auto px-6 py-16 grid md:grid-cols-3 gap-8">
          {page.benefits.map((b, i) => (
            <div key={i} className="rounded-xl border border-gray-100 p-6 shadow-sm">
              <h2 className="font-semibold text-lg text-emerald-900">{b.title}</h2>
              <p className="mt-2 text-gray-600 text-sm leading-relaxed">{b.body}</p>
            </div>
          ))}
        </section>
      ) : null}

      {page.tiers?.length > 0 ? (
        <section className="px-6 py-12 border-y border-gray-100 bg-emerald-50/50">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-xl font-bold text-emerald-900 mb-6">Loyalty tiers</h2>
            <div className="flex flex-wrap justify-center gap-4">
              {page.tiers.map((t) => (
                <div
                  key={t.code}
                  className="rounded-xl bg-white border border-emerald-100 px-5 py-4 min-w-[140px] shadow-sm"
                >
                  <p className="font-semibold text-emerald-900 capitalize">{t.name}</p>
                  <p className="text-xs text-gray-500 mt-1">{t.min_points_lifetime}+ lifetime points</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {page.plans.length > 0 ? (
        <section className="bg-gray-50 px-6 py-16">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-10">Membership plans</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {page.plans.map((plan) => (
                <article
                  key={plan.id}
                  className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col"
                >
                  <h3 className="font-semibold text-xl">{plan.name}</h3>
                  {plan.description ? (
                    <p className="mt-2 text-sm text-gray-600 flex-1">{plan.description}</p>
                  ) : (
                    <div className="flex-1" />
                  )}
                  {plan.included_services?.length > 0 ? (
                    <ul className="mt-3 text-xs text-gray-500 list-disc list-inside">
                      {plan.included_services.slice(0, 4).map((s, i) => (
                        <li key={i}>{String(s)}</li>
                      ))}
                    </ul>
                  ) : null}
                  <p className="mt-4 text-2xl font-bold text-emerald-800">
                    {formatPrice(plan.price_pence)}
                    <span className="text-sm font-normal text-gray-500"> / {plan.billing_cycle}</span>
                  </p>
                  {plan.discount_percent > 0 ? (
                    <p className="text-sm text-emerald-700 mt-1">{plan.discount_percent}% member discount</p>
                  ) : null}
                  <a
                    href="#membership-interest"
                    className="mt-4 block text-center rounded-lg border border-emerald-700 text-emerald-800 text-sm font-semibold py-2 hover:bg-emerald-50"
                  >
                    Enquire about this plan
                  </a>
                </article>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      <section id="membership-interest" className="px-6 py-16 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold text-center text-gray-900 mb-2">Interested in joining?</h2>
        <p className="text-sm text-gray-500 text-center mb-6">
          Send us your details and we&apos;ll get back to you about membership.
        </p>
        <MembershipInterestForm tenantSlug={page.tenant_slug} />
      </section>

      <footer className="py-6 px-6 text-center text-xs text-gray-400 border-t">
        Powered by CustomerFlow AI
      </footer>
    </main>
  )
}
