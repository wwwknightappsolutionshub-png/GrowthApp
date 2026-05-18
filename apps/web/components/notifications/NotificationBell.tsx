'use client'

import { Bell, Check, X } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useRef } from 'react'

import { useNotificationSocket } from '../../lib/hooks/use-notification-socket'
import { useNotificationsStore } from '../../lib/stores/notifications'

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

export function NotificationBell() {
  useNotificationSocket()
  const isOpen = useNotificationsStore((s) => s.isOpen)
  const setOpen = useNotificationsStore((s) => s.setOpen)
  const items = useNotificationsStore((s) => s.items)
  const unread = useNotificationsStore((s) => s.unread)
  const markRead = useNotificationsStore((s) => s.markRead)
  const markAllRead = useNotificationsStore((s) => s.markAllRead)
  const archive = useNotificationsStore((s) => s.archive)
  const hydrate = useNotificationsStore((s) => s.hydrate)

  const popoverRef = useRef<HTMLDivElement>(null)

  // Initial hydrate so the bell shows the unread count even if the WS hasn't
  // connected yet.
  useEffect(() => {
    void hydrate()
  }, [hydrate])

  // Click outside to close.
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    window.addEventListener('mousedown', handler)
    return () => window.removeEventListener('mousedown', handler)
  }, [isOpen, setOpen])

  return (
    <div className="relative" ref={popoverRef}>
      <button
        type="button"
        onClick={() => setOpen(!isOpen)}
        className="relative p-2 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-h-[28rem] bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden z-50 flex flex-col">
          <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-bold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard/notifications"
                onClick={() => setOpen(false)}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                View all
              </Link>
              <button
                type="button"
                onClick={() => void markAllRead()}
                disabled={unread === 0}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 disabled:text-gray-300 disabled:cursor-not-allowed"
              >
                Mark all read
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto">
            {items.length === 0 && (
              <div className="px-4 py-12 text-center text-sm text-gray-400">
                You're all caught up.
              </div>
            )}
            <ul className="divide-y divide-gray-100">
              {items.map((n) => {
                const unreadRow = !n.read_at
                const item = (
                  <div className="flex items-start gap-3 px-4 py-3 group hover:bg-gray-50 cursor-pointer">
                    <div
                      className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                        unreadRow ? 'bg-blue-500' : 'bg-transparent'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-sm leading-snug ${
                          unreadRow ? 'font-semibold text-gray-900' : 'text-gray-700'
                        }`}
                      >
                        {n.title}
                      </p>
                      {n.body && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                      )}
                      <p className="text-[10px] text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {unreadRow && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            void markRead(n.id)
                          }}
                          className="p-1 rounded text-gray-400 hover:text-emerald-600 hover:bg-emerald-50"
                          aria-label="Mark read"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          void archive(n.id)
                        }}
                        className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50"
                        aria-label="Dismiss"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )
                return (
                  <li key={n.id}>
                    {n.link ? (
                      <Link
                        href={n.link}
                        onClick={() => {
                          if (unreadRow) void markRead(n.id)
                          setOpen(false)
                        }}
                      >
                        {item}
                      </Link>
                    ) : (
                      <div
                        onClick={() => {
                          if (unreadRow) void markRead(n.id)
                        }}
                      >
                        {item}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
