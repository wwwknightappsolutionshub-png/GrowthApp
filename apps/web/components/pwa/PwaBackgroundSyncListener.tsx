'use client'

import { useEffect } from 'react'
import { drainSyncQueue } from '@/lib/pwa/background-sync'

/** Replays queued mutations when the service worker background sync fires. */
export function PwaBackgroundSyncListener() {
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return

    const onMessage = (event: MessageEvent) => {
      if (event.data?.type !== 'CF_SYNC_QUEUE') return
      const items = drainSyncQueue()
      items.forEach((item) => {
        void fetch(item.url, {
          method: item.method,
          headers: { 'Content-Type': 'application/json' },
          body: item.body,
          credentials: 'include',
        }).catch(() => {})
      })
    }

    navigator.serviceWorker.addEventListener('message', onMessage)
    return () => navigator.serviceWorker.removeEventListener('message', onMessage)
  }, [])

  return null
}
