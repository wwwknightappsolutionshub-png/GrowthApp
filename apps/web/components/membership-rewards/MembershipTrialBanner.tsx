'use client'

import Link from 'next/link'
import { Clock, Sparkles, Tag } from 'lucide-react'

import type { MembershipTrialStatus } from '@/lib/api-client'

export function MembershipTrialBanner({ trial }: { trial: MembershipTrialStatus }) {
  if (trial.show_winback_banner) {
    return (
      <div className="rounded-xl border border-brand-teal-500/40 bg-gradient-to-r from-brand-teal-950/80 to-brand-forest-900 p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <Tag className="w-5 h-5 text-brand-teal-300 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-white">
              {trial.winback_discount_percent}% off Membership &amp; Rewards
            </p>
            <p className="text-xs text-brand-teal-100/75 mt-1">
              Your trial ended. Resubscribe to restore plans, points, and your public memberships page.
            </p>
          </div>
        </div>
        <Link
          href={trial.upgrade_url}
          className="shrink-0 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500"
        >
          Claim offer
        </Link>
      </div>
    )
  }

  if (!trial.on_trial) return null

  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2 text-sm text-amber-100">
        <Clock className="w-4 h-4 shrink-0" />
        <span>
          <strong>Trial active</strong> — {trial.days_remaining} day
          {trial.days_remaining === 1 ? '' : 's'} left
          {trial.trial_ends_at
            ? ` (ends ${new Date(trial.trial_ends_at).toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'short',
              })})`
            : ''}
        </span>
      </div>
      <Link
        href={trial.setup_url}
        className="inline-flex items-center gap-1 text-sm font-semibold text-amber-200 hover:text-white"
      >
        <Sparkles className="w-4 h-4" />
        Set up now
      </Link>
    </div>
  )
}
