import type { ReactNode } from 'react'

export default function OnboardingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh overflow-y-auto overscroll-y-auto bg-gradient-to-b from-slate-50 via-white to-brand-teal-50/40 px-4 py-8 pb-32 sm:px-8 sm:py-10">
      <div className="mx-auto max-w-5xl">{children}</div>
    </div>
  )
}
