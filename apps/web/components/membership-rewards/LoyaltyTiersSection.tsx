'use client'

import { useState } from 'react'
import { membershipRewards } from '@/lib/api-client'

type Tier = {
  code: string
  name: string
  min_points_lifetime: number
  benefits: unknown[]
}

const TIER_STYLES: Record<string, string> = {
  bronze: 'border-amber-700/40 bg-amber-50 hover:bg-amber-100',
  silver: 'border-slate-400/50 bg-slate-50 hover:bg-slate-100',
  gold: 'border-yellow-500/50 bg-yellow-50 hover:bg-yellow-100',
  platinum: 'border-violet-400/50 bg-violet-50 hover:bg-violet-100',
}

export function LoyaltyTiersSection({
  tenantSlug,
  tiers,
}: {
  tenantSlug: string
  tiers: Tier[]
}) {
  const [selectedTier, setSelectedTier] = useState<Tier | null>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [submittedEmail, setSubmittedEmail] = useState('')
  const [enrollResult, setEnrollResult] = useState<{
    signup_bonus_points: number
    points_balance: number
    rewards_email_sent?: boolean
  } | null>(null)

  function closeModal() {
    setSelectedTier(null)
    setStatus('idle')
    setErrorMessage(null)
    setEnrollResult(null)
    setSubmittedEmail('')
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedTier) return
    setStatus('loading')
    setErrorMessage(null)
    try {
      const res = await membershipRewards.submitLoyaltyEnroll(tenantSlug, {
        name,
        email: email.trim(),
        phone: phone.trim() || undefined,
        tier_code: selectedTier.code,
      })
      setSubmittedEmail(email.trim())
      setEnrollResult({
        signup_bonus_points: res.data.signup_bonus_points,
        points_balance: res.data.points_balance,
        rewards_email_sent: res.data.rewards_email_sent,
      })
      setStatus('done')
      setName('')
      setEmail('')
      setPhone('')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } }
      const detail = axiosErr?.response?.data?.detail
      const status = axiosErr?.response?.status
      setStatus('error')
      if (typeof detail === 'string' && detail.trim()) {
        setErrorMessage(detail)
      } else if (status) {
        setErrorMessage(`Request failed (${status}). Please try again.`)
      } else {
        setErrorMessage('Something went wrong. Please try again.')
      }
    }
  }

  return (
    <>
      <section className="px-6 py-14 border-y border-gray-100 bg-emerald-50/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-emerald-900 text-center">Loyalty program</h2>
          <p className="mt-3 text-gray-600 text-center max-w-2xl mx-auto leading-relaxed">
            Our loyalty program is completely free. You choose how committed you want to be — from
            Bronze through Platinum — and we reward you every step of the way with points, perks, and
            recognition on our leaderboard.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            {tiers.map((t) => (
              <button
                key={t.code}
                type="button"
                onClick={() => setSelectedTier(t)}
                className={`rounded-xl border px-5 py-4 min-w-[140px] shadow-sm text-left transition-colors cursor-pointer ${
                  TIER_STYLES[t.code] ?? 'border-emerald-100 bg-white hover:bg-emerald-50'
                }`}
              >
                <p className="font-semibold text-emerald-900 capitalize">{t.name}</p>
                <p className="text-xs text-gray-600 mt-1">{t.min_points_lifetime}+ lifetime points</p>
                <p className="text-xs text-emerald-800 mt-2 font-medium">Tap to join →</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {selectedTier ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="loyalty-enroll-title"
        >
          <div className="surface-light w-full max-w-md rounded-xl bg-white p-6 shadow-xl text-gray-900">
            {status === 'done' ? (
              <>
                <h3 id="loyalty-enroll-title" className="text-lg font-bold text-emerald-900">
                  You&apos;re in!
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Welcome to the {selectedTier.name} tier. We&apos;ve added you to our loyalty
                  leaderboard
                  {enrollResult && enrollResult.signup_bonus_points > 0
                    ? ` with ${enrollResult.signup_bonus_points} membership points (${enrollResult.points_balance} total)`
                    : ''}
                  {submittedEmail && enrollResult?.rewards_email_sent !== false
                    ? `. Check ${submittedEmail} for your rewards wallet link, QR code, and login details`
                    : submittedEmail
                      ? `. We saved your details — ask staff for your rewards wallet link if you don't see an email shortly`
                      : ''}
                  . Start earning more on your next visit.
                </p>
                <button
                  type="button"
                  onClick={closeModal}
                  className="mt-6 w-full rounded-lg bg-emerald-800 text-white font-semibold py-2.5 text-sm"
                >
                  Close
                </button>
              </>
            ) : (
              <>
                <h3 id="loyalty-enroll-title" className="text-lg font-bold text-emerald-900">
                  Join {selectedTier.name} tier
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Free to join. We&apos;ll create your rewards wallet and email you a login link with a QR code.
                </p>
                <form onSubmit={onSubmit} className="mt-4 space-y-3">
                  <input
                    required
                    placeholder="Full name *"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
                  />
                  <input
                    type="email"
                    required
                    placeholder="Email *"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
                  />
                  <input
                    placeholder="Phone (optional)"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
                  />
                  <p className="text-xs text-gray-500">
                    Email is required so we can send your rewards wallet link and prevent duplicate sign-ups.
                  </p>
                  {status === 'error' && (
                    <p className="text-sm text-red-600">{errorMessage ?? 'Something went wrong. Please try again.'}</p>
                  )}
                  <div className="flex gap-2 pt-1">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="flex-1 rounded-lg border border-gray-300 text-gray-700 py-2.5 text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={status === 'loading' || !email.trim() || !name.trim()}
                      className="flex-1 rounded-lg bg-emerald-800 text-white font-semibold py-2.5 text-sm hover:bg-emerald-900 disabled:opacity-50"
                    >
                      {status === 'loading' ? 'Submitting…' : 'Submit'}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      ) : null}
    </>
  )
}
