'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Globe, Sparkles, X } from 'lucide-react'
import { landingPages } from '@/lib/api-client'

const DISMISS_KEY = 'cf_landing_prompt_dismissed_until'

function dismissedUntil(): number {
  if (typeof window === 'undefined') return 0
  const v = localStorage.getItem(DISMISS_KEY)
  return v ? Number(v) : 0
}

function dismissForHours(hours: number) {
  localStorage.setItem(DISMISS_KEY, String(Date.now() + hours * 3600 * 1000))
}

type PageRow = { id: string; is_published: boolean }

export function useHasActiveLandingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['landing-pages-active-check'],
    queryFn: () => landingPages.list().then((r) => r.data as PageRow[]),
    staleTime: 60_000,
  })
  const hasActive = (data ?? []).some((p) => p.is_published)
  return { hasActive, isLoading, pages: data ?? [] }
}

export function LandingPagePromptBanner({ variant = 'dashboard' }: { variant?: 'dashboard' | 'modal' }) {
  const { hasActive, isLoading } = useHasActiveLandingPage()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (isLoading || hasActive) {
      setVisible(false)
      return
    }
    if (Date.now() < dismissedUntil()) {
      setVisible(false)
      return
    }
    setVisible(true)
  }, [hasActive, isLoading])

  if (!visible) return null

  const inner = (
    <>
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-brand-teal-400/20 flex items-center justify-center shrink-0">
          <Globe className="w-6 h-6 text-brand-teal-300" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold uppercase tracking-widest text-brand-teal-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Your #1 lead channel
          </p>
          <h3 className="mt-1 text-lg font-bold text-white">Publish your business page</h3>
          <p className="mt-2 text-sm text-brand-teal-100/75 leading-relaxed">
            Your branded business page is your primary funnel for new leads — it captures enquiries
            24/7 while you work jobs. Set it up in the site builder and share your QR code.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href="/dashboard/site-builder"
              className="inline-flex items-center rounded-lg bg-brand-teal-400 px-4 py-2 text-sm font-bold text-brand-forest-950 hover:bg-brand-teal-300"
            >
              Open site builder
            </Link>
            <button
              type="button"
              onClick={() => {
                dismissForHours(24)
                setVisible(false)
              }}
              className="inline-flex items-center rounded-lg border border-brand-forest-700 px-4 py-2 text-sm text-brand-teal-100/80 hover:bg-brand-forest-900"
            >
              Remind me tomorrow
            </button>
          </div>
        </div>
        <button
          type="button"
          aria-label="Dismiss"
          onClick={() => {
            dismissForHours(8)
            setVisible(false)
          }}
          className="text-brand-teal-100/50 hover:text-white shrink-0"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </>
  )

  if (variant === 'modal') {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
        <div className="max-w-lg w-full rounded-2xl border border-brand-forest-700 bg-brand-forest-950 p-6 shadow-2xl">
          {inner}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-brand-teal-400/30 bg-brand-forest-900/90 p-5 shadow-sm">
      {inner}
    </div>
  )
}

/** Exit-intent: mouse leaves viewport toward top */
export function LandingPageExitIntent() {
  const { hasActive, isLoading } = useHasActiveLandingPage()
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (isLoading || hasActive) return
    if (Date.now() < dismissedUntil()) return

    const onLeave = (e: MouseEvent) => {
      if (e.clientY <= 0) setShow(true)
    }
    document.addEventListener('mouseout', onLeave)
    return () => document.removeEventListener('mouseout', onLeave)
  }, [hasActive, isLoading])

  if (!show) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
      <div className="max-w-lg w-full rounded-2xl border border-brand-forest-700 bg-brand-forest-950 p-6 shadow-2xl relative">
        <button
          type="button"
          aria-label="Close"
          onClick={() => setShow(false)}
          className="absolute right-4 top-4 text-brand-teal-100/50 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>
        <LandingPagePromptBanner variant="dashboard" />
      </div>
    </div>
  )
}
