'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { pwaEngagement } from '@/lib/api-client'

const EXIT_SENT_KEY = 'cf:pwa:exit-email-sent'

/** Fire a one-per-session exit-intent email when leaving the dashboard without PWA installed. */
export function PWAExitMonitor() {
  const pathname = usePathname()

  useEffect(() => {
    if (!pathname?.startsWith('/dashboard')) return
    if (typeof window === 'undefined') return
    if (window.matchMedia('(display-mode: standalone)').matches) return
    if (window.localStorage.getItem(EXIT_SENT_KEY) === '1') return

    const onLeave = () => {
      if (window.localStorage.getItem(EXIT_SENT_KEY) === '1') return
      window.localStorage.setItem(EXIT_SENT_KEY, '1')
      window.dispatchEvent(new CustomEvent('cf:pwa-exit-intent'))
      void pwaEngagement.recordExitIntent().catch(() => {})
    }

    const onMouseOut = (event: MouseEvent) => {
      if (event.clientY <= 0) onLeave()
    }

    window.addEventListener('mouseout', onMouseOut)
    window.addEventListener('pagehide', onLeave)
    return () => {
      window.removeEventListener('mouseout', onMouseOut)
      window.removeEventListener('pagehide', onLeave)
    }
  }, [pathname])

  return null
}
