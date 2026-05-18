import type { ReactNode } from 'react'

export default function OnboardingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-brand-teal-50/40 py-10 px-4 sm:px-8">
      <div className="mx-auto max-w-5xl">{children}</div>
    </div>
  )
}
