'use client'

import type { ReactNode } from 'react'

type Props = {
  tenantName: string
  subtitle?: string
  accent?: string
  children: ReactNode
}

export function PublicBookShell({ tenantName, subtitle, accent = '#166534', children }: Props) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <header
        className="border-b border-white/10 px-6 py-8 text-white"
        style={{ background: `linear-gradient(135deg, ${accent} 0%, #0f172a 100%)` }}
      >
        <div className="max-w-lg mx-auto">
          <p className="text-xs uppercase tracking-widest text-white/70 font-semibold">Online booking</p>
          <h1 className="text-2xl sm:text-3xl font-bold mt-1">{tenantName}</h1>
          {subtitle ? <p className="text-sm text-white/80 mt-2">{subtitle}</p> : null}
        </div>
      </header>
      <main className="max-w-lg mx-auto px-6 py-8 -mt-4">
        <div className="rounded-2xl bg-white shadow-xl border border-slate-200/80 p-6 sm:p-8">{children}</div>
      </main>
      <footer className="text-center text-xs text-slate-500 pb-8">Powered by CustomerFlow</footer>
    </div>
  )
}
