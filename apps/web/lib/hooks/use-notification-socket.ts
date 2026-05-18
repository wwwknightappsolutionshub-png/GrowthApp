'use client'

import { useEffect, useRef } from 'react'

import { useNotificationsStore, type Notification } from '../stores/notifications'

/**
 * Maintains a WebSocket connection to /api/v1/notifications/ws and feeds
 * incoming notifications into the Zustand store. Reconnects with exponential
 * backoff on close/error.
 *
 * Auth: relies on the same-origin httpOnly access_token cookie. The Next.js
 * rewrite in next.config.js proxies `/api/v1/*` to the FastAPI server, so the
 * cookie is sent automatically with the upgrade request.
 */
export function useNotificationSocket() {
  const ingest = useNotificationsStore((s) => s.ingest)
  const setUnread = useNotificationsStore((s) => s.setUnread)
  const hydrate = useNotificationsStore((s) => s.hydrate)
  const attemptRef = useRef(0)

  useEffect(() => {
    let socket: WebSocket | null = null
    let closed = false
    let reconnectTimer: number | null = null

    const connect = () => {
      // The dev preview uses `ws://`; production uses `wss://` via the Caddy/nginx proxy.
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${window.location.host}/api/v1/notifications/ws`
      socket = new WebSocket(url)

      socket.addEventListener('open', () => {
        attemptRef.current = 0
        // Hydrate the bell from the REST API on connect so we have history.
        void hydrate()
      })

      socket.addEventListener('message', (event) => {
        try {
          const msg = JSON.parse(event.data) as
            | { type: 'hello'; unread: number; total: number }
            | { type: 'notification'; data: Notification }
            | { type: 'ping' }
          if (msg.type === 'hello') {
            setUnread(msg.unread)
          } else if (msg.type === 'notification') {
            ingest(msg.data)
          }
        } catch (err) {
          console.warn('Unparseable WS message', err)
        }
      })

      socket.addEventListener('close', () => {
        if (closed) return
        attemptRef.current += 1
        const delay = Math.min(30_000, 1000 * 2 ** Math.min(attemptRef.current, 5))
        reconnectTimer = window.setTimeout(connect, delay)
      })

      socket.addEventListener('error', () => {
        try {
          socket?.close()
        } catch {
          // ignore
        }
      })
    }

    connect()

    return () => {
      closed = true
      if (reconnectTimer) window.clearTimeout(reconnectTimer)
      try {
        socket?.close()
      } catch {
        // ignore
      }
    }
  }, [hydrate, ingest, setUnread])
}
