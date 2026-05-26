'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import { Download, Gift, Smartphone, X } from 'lucide-react'
import { enablePushAutomatically } from '@/lib/pwa/push-subscribe'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

const DISMISS_KEY = 'cf:pwa:install-dismissed-at'
const HARD_DISMISS_KEY = 'cf:pwa:install-dismissed-hard'
const INSTALLED_KEY = 'cf:pwa:installed'
const HIGH_VALUE_KEY = 'cf:pwa:high-value-prompt'
const REMIND_AFTER_MS = 1000 * 60 * 60 * 24
const GATE_DELAY_MS = 2500

function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(max-width: 768px), (pointer: coarse)').matches
}

function isStandaloneMode(): boolean {
  if (typeof window === 'undefined') return false
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function isIosSafari(): boolean {
  if (typeof window === 'undefined') return false
  const ua = window.navigator.userAgent
  return /iphone|ipad|ipod/i.test(ua) && /safari/i.test(ua) && !/crios|fxios|edgios/i.test(ua)
}

function canShowAgain(): boolean {
  if (typeof window === 'undefined') return false
  if (window.localStorage.getItem(HARD_DISMISS_KEY) === '1') return false
  const dismissedAt = Number(window.localStorage.getItem(DISMISS_KEY) || 0)
  return !dismissedAt || Date.now() - dismissedAt > REMIND_AFTER_MS
}

function PWAInstallManagerInner() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const forceInstall = searchParams?.get('install') === '1'
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  const [isStandalone, setIsStandalone] = useState(false)
  const [visible, setVisible] = useState(false)
  const [iosSafari, setIosSafari] = useState(false)
  const [pushMessage, setPushMessage] = useState<string | null>(null)
  const [gateReady, setGateReady] = useState(false)

  const isAppArea = pathname?.startsWith('/dashboard') || pathname?.startsWith('/admin')
  const isAuthPage = pathname?.startsWith('/login') || pathname?.startsWith('/register')

  useEffect(() => {
    if (!('serviceWorker' in navigator) || process.env.NODE_ENV === 'test') return
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  }, [])

  useEffect(() => {
    const updateState = () => {
      setIsMobile(isMobileDevice())
      setIsStandalone(isStandaloneMode())
      setIosSafari(isIosSafari())
    }
    updateState()
    window.addEventListener('resize', updateState)
    window.addEventListener('appinstalled', () => {
      window.localStorage.setItem(INSTALLED_KEY, '1')
      setIsStandalone(true)
      setVisible(false)
      void enablePushAutomatically({ force: true, silent: true }).then((res) => {
        if (res.ok) setPushMessage(res.message)
      })
    })
    return () => window.removeEventListener('resize', updateState)
  }, [])

  useEffect(() => {
    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
    return () => window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  }, [])

  useEffect(() => {
    if (!isAppArea || isStandalone) return
    const timer = window.setTimeout(() => setGateReady(true), GATE_DELAY_MS)
    return () => window.clearTimeout(timer)
  }, [isAppArea, isStandalone, pathname])

  useEffect(() => {
    if (isAppArea && !isStandalone) {
      void enablePushAutomatically({ silent: true }).then((res) => {
        if (res.ok) setPushMessage(res.message)
      })
    }
  }, [isAppArea, isStandalone, pathname])

  useEffect(() => {
    const onExitIntent = () => {
      if (!isAppArea || isStandalone || !isMobile) return
      if (canShowAgain()) setVisible(true)
    }
    window.addEventListener('cf:pwa-exit-intent', onExitIntent)
    return () => window.removeEventListener('cf:pwa-exit-intent', onExitIntent)
  }, [isAppArea, isStandalone, isMobile])

  useEffect(() => {
    const onHighValue = () => {
      if (isStandalone || !isMobile) return
      window.localStorage.setItem(HIGH_VALUE_KEY, '1')
      setVisible(true)
    }
    window.addEventListener('cf:pwa-high-value', onHighValue)
    return () => window.removeEventListener('cf:pwa-high-value', onHighValue)
  }, [isStandalone, isMobile])

  useEffect(() => {
    if (forceInstall) {
      setVisible(true)
      return
    }
    if (!isMobile || isStandalone || window.localStorage.getItem(INSTALLED_KEY) === '1') {
      setVisible(false)
      return
    }
    if (isAppArea) {
      const highValue = window.localStorage.getItem(HIGH_VALUE_KEY) === '1'
      setVisible(gateReady && (highValue || canShowAgain()))
      return
    }
    setVisible(canShowAgain() && !isAuthPage)
  }, [forceInstall, isAppArea, isAuthPage, isMobile, isStandalone, pathname, gateReady])

  const mode = useMemo<'gate' | 'banner'>(() => (isAppArea ? 'gate' : 'banner'), [isAppArea])

  const dismiss = (hard = false) => {
    window.localStorage.setItem(DISMISS_KEY, String(Date.now()))
    if (hard) window.localStorage.setItem(HARD_DISMISS_KEY, '1')
    setVisible(false)
  }

  const install = async () => {
    if (installPrompt) {
      await installPrompt.prompt()
      const choice = await installPrompt.userChoice
      if (choice.outcome === 'accepted') {
        window.localStorage.setItem(INSTALLED_KEY, '1')
        setVisible(false)
        const push = await enablePushAutomatically({ force: true })
        if (push.message) setPushMessage(push.message)
      } else {
        dismiss()
      }
      setInstallPrompt(null)
      return
    }
    setVisible(true)
  }

  if ((!visible && !forceInstall) || (!forceInstall && !isMobile) || isStandalone) return null

  const walletCopy =
    'Give your customers a rewards wallet they can install — then get pinged when a new lead arrives or a booking is due.'

  if (mode === 'gate') {
    return (
      <div className="fixed inset-0 z-[80] flex items-end bg-black/60 p-3 backdrop-blur-sm sm:items-center sm:justify-center">
        <section className="w-full rounded-2xl border border-white/10 bg-brand-forest-950 p-5 text-white shadow-2xl sm:max-w-md">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-teal-400 text-brand-teal-foreground">
                <Gift className="h-5 w-5" />
              </span>
              <div>
                <h2 className="font-display text-lg font-bold">Launch your customer wallet app</h2>
                <p className="text-xs text-white/55">Membership &amp; Rewards on their home screen</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => dismiss()}
              className="rounded-md p-1 text-white/45 hover:bg-white/10 hover:text-white"
              aria-label="Continue in browser"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="text-sm leading-relaxed text-white/72">{walletCopy}</p>
          {iosSafari && (
            <div className="mt-4 rounded-xl border border-brand-teal-300/25 bg-brand-teal-300/10 p-3 text-xs text-brand-teal-50">
              On iPhone: tap Share, then choose <strong>Add to Home Screen</strong>.
            </div>
          )}
          {pushMessage && (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-white/70">
              {pushMessage}
            </div>
          )}
          <div className="mt-5 grid gap-2">
            <button
              type="button"
              onClick={() => void install()}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-teal-400 px-4 py-3 text-sm font-bold text-brand-teal-foreground hover:bg-brand-teal-300"
            >
              <Download className="h-4 w-4" />
              Install workspace app
            </button>
            <a
              href="/dashboard/membership-rewards"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-brand-teal-300/25 px-4 py-3 text-sm font-semibold text-brand-teal-100 hover:bg-brand-teal-300/10"
            >
              <Smartphone className="h-4 w-4" />
              Set up customer wallet
            </a>
            <button
              type="button"
              onClick={() => dismiss()}
              className="rounded-lg border border-white/10 px-4 py-3 text-sm font-semibold text-white/70 hover:bg-white/5 hover:text-white"
            >
              Continue in browser
            </button>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="fixed inset-x-3 bottom-3 z-[70] rounded-2xl border border-brand-forest-700 bg-brand-forest-950 p-4 text-white shadow-2xl">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-teal-400 text-brand-teal-foreground">
          <Gift className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-bold">Give customers a wallet app on their phone</h2>
          <p className="mt-1 text-xs leading-relaxed text-white/65">{walletCopy}</p>
          {iosSafari && (
            <p className="mt-2 text-[11px] text-brand-teal-100">
              iPhone: tap Share, then Add to Home Screen.
            </p>
          )}
          {pushMessage && <p className="mt-2 text-[11px] text-white/60">{pushMessage}</p>}
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void install()}
              className="rounded-md bg-brand-teal-400 px-3 py-2 text-xs font-bold text-brand-teal-foreground"
            >
              Install app
            </button>
            <button
              type="button"
              onClick={() => dismiss()}
              className="rounded-md border border-white/10 px-3 py-2 text-xs font-semibold text-white/65"
            >
              Remind me later
            </button>
          </div>
        </div>
        <button
          type="button"
          onClick={() => dismiss(true)}
          className="rounded-md p-1 text-white/40 hover:bg-white/10 hover:text-white"
          aria-label="Dismiss install prompt"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

export function PWAInstallManager() {
  return (
    <Suspense fallback={null}>
      <PWAInstallManagerInner />
    </Suspense>
  )
}

/** Call from dashboard after first lead or booking is created. */
export function triggerHighValuePwaPrompt() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('cf:pwa-high-value'))
}
