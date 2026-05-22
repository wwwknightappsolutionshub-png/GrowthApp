'use client'

import { firstName, greetingPhrase } from '@/lib/greeting'

export function TenantWelcomeHeader({
  tenantName,
  userName,
  subtitle = "Let's move the business to the next level today",
}: {
  tenantName?: string | null
  userName?: string | null
  subtitle?: string
}) {
  const greet = greetingPhrase()
  const who = firstName(userName)
  const business = tenantName?.trim()

  return (
    <header className="rounded-2xl border border-brand-forest-800 bg-gradient-to-br from-brand-forest-950 via-brand-forest-900 to-brand-forest-950 p-6 sm:p-8 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-widest text-brand-teal-300/90">
        {greet}
      </p>
      <h1 className="mt-2 font-display text-2xl sm:text-3xl font-bold text-white">
        Welcome, {who}
        {business ? (
          <span className="block text-lg sm:text-xl font-semibold text-brand-teal-100/90 mt-1">
            {business}
          </span>
        ) : null}
      </h1>
      <p className="mt-3 text-sm sm:text-base text-brand-teal-100/75 max-w-2xl">{subtitle}</p>
    </header>
  )
}
