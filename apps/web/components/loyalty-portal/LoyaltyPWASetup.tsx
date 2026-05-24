'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Download, Smartphone, X } from 'lucide-react'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

const DISMISS_KEY = 'loyalty:pwa:install-dismissed'

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

function LoyaltyPWASetupInner() {
  const searchParams = useSearchParams()
  const forceInstall = searchParams?.get('install') === '1'
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)
  const [iosSafari, setIosSafari] = useState(false)

  useEffect(() => {
    if (!('serviceWorker' in navigator) || process.env.NODE_ENV === 'test') return
    navigator.serviceWorker.register('/rewards/sw.js').catch(() => {})
  }, [])

  useEffect(() => {
    if (isStandaloneMode()) return
    setIosSafari(isIosSafari())
    if (!forceInstall && sessionStorage.getItem(DISMISS_KEY) === '1') return
    setVisible(true)

    const onBeforeInstall = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    return () => window.removeEventListener('beforeinstallprompt', onBeforeInstall)
  }, [forceInstall])

  async function install() {
    if (!installPrompt) return
    await installPrompt.prompt()
    const { outcome } = await installPrompt.userChoice
    if (outcome === 'accepted') {
      setVisible(false)
    }
    setInstallPrompt(null)
  }

  function dismiss() {
    sessionStorage.setItem(DISMISS_KEY, '1')
    setVisible(false)
  }

  if (!visible || isStandaloneMode()) return null

  return (
    <div className="fixed bottom-20 left-0 right-0 z-20 mx-auto max-w-lg px-4">
      <div className="card flex items-start gap-3 border-[var(--tenant-primary)]/20 bg-white shadow-lg">
        <Smartphone className="mt-0.5 h-5 w-5 shrink-0 text-[var(--tenant-primary)]" />
        <div className="flex-1 text-sm">
          <p className="font-semibold">Install rewards wallet</p>
          <p className="mt-1 text-slate-600">
            {iosSafari && !installPrompt
              ? 'Tap Share, then Add to Home Screen for quick access.'
              : 'Add this wallet to your home screen for one-tap access.'}
          </p>
          {installPrompt ? (
            <button type="button" className="btn-primary mt-3 text-xs" onClick={() => void install()}>
              <Download className="mr-1 inline h-4 w-4" />
              Install app
            </button>
          ) : null}
        </div>
        <button type="button" className="text-slate-400" aria-label="Dismiss" onClick={dismiss}>
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

export function LoyaltyPWASetup() {
  return (
    <Suspense fallback={null}>
      <LoyaltyPWASetupInner />
    </Suspense>
  )
}
