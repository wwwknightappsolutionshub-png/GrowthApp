'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { X } from 'lucide-react'

import type { MembershipTrialStatus } from '@/lib/api-client'

const DISMISS_KEY = 'mr-trial-urgency-dismissed'

export function MembershipTrialModal({
  trial,
  tenantId,
}: {
  trial: MembershipTrialStatus
  tenantId?: string
}) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!trial.show_urgency_modal || !trial.on_trial) {
      setOpen(false)
      return
    }
    const key = tenantId ? `${DISMISS_KEY}-${tenantId}` : DISMISS_KEY
    if (typeof window !== 'undefined' && window.localStorage.getItem(key) === '1') {
      return
    }
    setOpen(true)
  }, [trial.show_urgency_modal, trial.on_trial, tenantId])

  if (!open) return null

  function dismiss() {
    const key = tenantId ? `${DISMISS_KEY}-${tenantId}` : DISMISS_KEY
    window.localStorage.setItem(key, '1')
    setOpen(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div
        className="relative w-full max-w-md rounded-2xl border border-white/10 bg-brand-forest-950 p-6 shadow-xl"
        role="dialog"
        aria-labelledby="mr-trial-modal-title"
      >
        <button
          type="button"
          onClick={dismiss}
          className="absolute right-3 top-3 text-slate-400 hover:text-white"
          aria-label="Dismiss"
        >
          <X className="w-5 h-5" />
        </button>
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-400">Trial ending</p>
        <h2 id="mr-trial-modal-title" className="mt-2 text-xl font-bold text-white">
          {trial.days_remaining <= 1
            ? 'Your trial ends tomorrow'
            : 'Your trial is ending soon'}
        </h2>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed">
          Publish your <code className="text-brand-teal-300">/memberships</code> page and subscribe to keep
          loyalty points, tiers, and customer subscriptions active.
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <Link
            href={`${trial.setup_url}?section=landing`}
            onClick={dismiss}
            className="w-full rounded-lg bg-brand-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-brand-teal-500"
          >
            Finish setup
          </Link>
          <Link
            href={trial.upgrade_url}
            onClick={dismiss}
            className="w-full rounded-lg border border-white/20 py-2.5 text-center text-sm text-white hover:bg-white/5"
          >
            Subscribe now
          </Link>
          <button
            type="button"
            onClick={dismiss}
            className="text-xs text-slate-500 hover:text-slate-300 mt-1"
          >
            Remind me later
          </button>
        </div>
      </div>
    </div>
  )
}
