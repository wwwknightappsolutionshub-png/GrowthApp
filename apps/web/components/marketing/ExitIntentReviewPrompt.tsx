'use client'

import { useEffect, useState } from 'react'

import { ShareReviewModal } from './ShareReviewModal'

const STORAGE_KEY = 'cf-exit-intent-review-shown'
const EXIT_INTENT_GRACE_MS = 8_000 // wait 8s after page load before arming
const FALLBACK_INACTIVITY_MS = 90_000 // 1m 30s of stillness → open as well

/**
 * Listens for an "exit-intent" gesture from the visitor and pops the review
 * capture modal.
 *
 * Two triggers:
 * - Mouse leaving the viewport upward (desktop).
 * - 90 seconds of total page inactivity (mobile fallback, where there is no
 *   exit-intent gesture).
 *
 * Fires at most once per browser session — we persist a flag in `sessionStorage`
 * so repeated navigations don't pester the visitor.
 */
export function ExitIntentReviewPrompt() {
  const [open, setOpen] = useState(false)
  const [armed, setArmed] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      if (window.sessionStorage.getItem(STORAGE_KEY)) return
    } catch {
      // sessionStorage might be blocked — fall through and use the trigger anyway.
    }

    const armTimer = window.setTimeout(() => setArmed(true), EXIT_INTENT_GRACE_MS)
    return () => window.clearTimeout(armTimer)
  }, [])

  useEffect(() => {
    if (!armed || open) return

    const trigger = () => {
      setOpen(true)
      try {
        window.sessionStorage.setItem(STORAGE_KEY, '1')
      } catch {
        /* ignore */
      }
    }

    function handleMouseLeave(event: MouseEvent) {
      // Pointer left through the top of the viewport.
      if (event.clientY <= 0 && event.relatedTarget === null) {
        trigger()
      }
    }

    let inactivityTimer: number | null = window.setTimeout(trigger, FALLBACK_INACTIVITY_MS)

    function resetInactivity() {
      if (inactivityTimer !== null) {
        window.clearTimeout(inactivityTimer)
        inactivityTimer = window.setTimeout(trigger, FALLBACK_INACTIVITY_MS)
      }
    }

    document.addEventListener('mouseleave', handleMouseLeave)
    document.addEventListener('mousemove', resetInactivity, { passive: true })
    document.addEventListener('scroll', resetInactivity, { passive: true })
    document.addEventListener('touchstart', resetInactivity, { passive: true })

    return () => {
      document.removeEventListener('mouseleave', handleMouseLeave)
      document.removeEventListener('mousemove', resetInactivity)
      document.removeEventListener('scroll', resetInactivity)
      document.removeEventListener('touchstart', resetInactivity)
      if (inactivityTimer !== null) window.clearTimeout(inactivityTimer)
    }
  }, [armed, open])

  return (
    <ShareReviewModal
      open={open}
      source="exit_intent"
      onClose={() => setOpen(false)}
    />
  )
}
