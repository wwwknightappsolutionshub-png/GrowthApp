'use client'

import type { ReactNode } from 'react'
import { Calendar, Gift, Star } from 'lucide-react'

export type PublicBookVariant = 'booking' | 'refer' | 'review'

const VARIANT_META: Record<
  PublicBookVariant,
  { eyebrow: string; icon: typeof Calendar; headerClass: string }
> = {
  booking: {
    eyebrow: 'Book appointment',
    icon: Calendar,
    headerClass: 'from-emerald-800 to-slate-900',
  },
  refer: {
    eyebrow: 'Refer & Win',
    icon: Gift,
    headerClass: 'from-violet-800 to-slate-900',
  },
  review: {
    eyebrow: 'Review on Google',
    icon: Star,
    headerClass: 'from-amber-700 to-slate-900',
  },
}

type Props = {
  tenantName: string
  subtitle?: string
  accent?: string
  variant?: PublicBookVariant
  children: ReactNode
}

export function PublicBookShell({
  tenantName,
  subtitle,
  accent = '#166534',
  variant = 'booking',
  children,
}: Props) {
  const meta = VARIANT_META[variant]
  const Icon = meta.icon

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <header
        className={`border-b border-white/10 px-6 py-8 text-white bg-gradient-to-br ${meta.headerClass}`}
        style={
          variant === 'booking'
            ? { background: `linear-gradient(135deg, ${accent} 0%, #0f172a 100%)` }
            : undefined
        }
      >
        <div className="max-w-lg mx-auto">
          <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-white/80 font-semibold">
            <Icon className="w-4 h-4" />
            {meta.eyebrow}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold mt-2">{tenantName}</h1>
          {subtitle ? <p className="text-sm text-white/85 mt-2">{subtitle}</p> : null}
        </div>
      </header>
      <main className="max-w-lg mx-auto px-6 py-8 -mt-4">
        <div className="rounded-2xl bg-white shadow-xl border border-slate-200/80 p-6 sm:p-8">{children}</div>
      </main>
      <footer className="text-center text-xs text-slate-500 pb-8">Powered by CustomerFlow</footer>
    </div>
  )
}
