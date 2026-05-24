'use client'

import Link from 'next/link'
import { Crown, ExternalLink, Gift, Star, Users } from 'lucide-react'
import type { LoyaltyPortalUpsell } from '@/lib/api-client'
import { rewardsPath } from '@/lib/loyalty-portal-auth'
import { formatCurrency } from '@/lib/utils'

type Props = {
  tenant: string
  upsell: LoyaltyPortalUpsell
}

export function LoyaltyUpsellSection({ tenant, upsell }: Props) {
  return (
    <div className="space-y-3">
      {upsell.active_subscription ? (
        <section className="card card-membership">
          <div className="flex items-start gap-3">
            <Crown className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">Your membership</p>
              <p className="mt-1 font-semibold text-[hsl(var(--foreground))]">
                {upsell.active_subscription.plan_name}
              </p>
              {upsell.active_subscription.plan_description ? (
                <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
                  {upsell.active_subscription.plan_description}
                </p>
              ) : null}
              <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                {formatCurrency(upsell.active_subscription.price_pence / 100)} /{' '}
                {upsell.active_subscription.billing_cycle}
                {upsell.active_subscription.current_period_end
                  ? ` · renews ${new Date(upsell.active_subscription.current_period_end).toLocaleDateString('en-GB')}`
                  : ''}
              </p>
              {upsell.active_subscription.benefits.length > 0 ? (
                <ul className="mt-2 space-y-1 text-sm text-[hsl(var(--foreground))]">
                  {upsell.active_subscription.benefits.map((b) => (
                    <li key={b}>• {b}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>
        </section>
      ) : upsell.has_membership_plans ? (
        <section className="card card-accent">
          <div className="flex items-start gap-3">
            <Gift className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
            <div className="flex-1">
              <p className="font-semibold text-brand">Upgrade membership</p>
              <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
                Unlock exclusive discounts, bonus points, and member-only perks.
              </p>
              <a
                href={upsell.memberships_url}
                className="btn-primary mt-3 inline-flex items-center gap-1"
              >
                View plans
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        </section>
      ) : null}

      {upsell.google_review_available && upsell.google_review_url ? (
        <section className="card card-review">
          <div className="flex items-start gap-3">
            <Star className="mt-0.5 h-5 w-5 shrink-0 text-accent" fill="currentColor" />
            <div className="flex-1">
              <p className="font-semibold text-brand">Review &amp; win</p>
              <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
                Leave us a Google review and earn loyalty points when your review is submitted.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  href={upsell.google_review_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-accent inline-flex items-center gap-1"
                >
                  Review now
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
                <Link href={rewardsPath(tenant, 'profile')} className="btn-secondary inline-flex text-xs">
                  Show QR code
                </Link>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {upsell.targeted_offers.map((offer) => (
        <section key={`${offer.type}-${offer.title}`} className="card">
          <p className="font-semibold text-brand">{offer.title}</p>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">{offer.body}</p>
          <a href={offer.cta_url} className="mt-3 inline-flex text-sm font-semibold text-accent">
            {offer.cta_label} →
          </a>
        </section>
      ))}

      <section className="card card-accent flex items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <Users className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
          <div>
            <p className="font-semibold text-brand">Refer &amp; Win</p>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">Refer friends and earn bonus points.</p>
          </div>
        </div>
        <Link href={rewardsPath(tenant, 'refer')} className="btn-secondary shrink-0 text-xs">
          Refer
        </Link>
      </section>
    </div>
  )
}
