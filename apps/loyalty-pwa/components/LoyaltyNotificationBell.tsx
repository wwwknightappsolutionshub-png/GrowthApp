'use client'

import { Bell, Check } from 'lucide-react'
import Link from 'next/link'
import { useCallback, useEffect, useRef, useState } from 'react'

import { loyaltyPortal, type WalletNotification } from '@/lib/api-client'

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

function walletPath(tenant: string, subpath: string | null): string | undefined {
  if (!subpath) return undefined
  return `/${tenant}/${subpath.replace(/^\//, '')}`
}

function isAuthed(tenant: string): boolean {
  if (typeof window === 'undefined') return false
  return Boolean(localStorage.getItem(`loyalty:${tenant}:token`))
}

export function LoyaltyNotificationBell({ tenant }: { tenant: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const [items, setItems] = useState<WalletNotification[]>([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(false)
  const [authed, setAuthed] = useState(false)
  const popoverRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setAuthed(isAuthed(tenant))
  }, [tenant])

  const refreshUnread = useCallback(async () => {
    if (!isAuthed(tenant)) return
    try {
      const res = await loyaltyPortal.unreadCount(tenant)
      setUnread(res.data.unread)
    } catch {
      // ignore polling errors
    }
  }, [tenant])

  const loadNotifications = useCallback(async () => {
    if (!isAuthed(tenant)) return
    setLoading(true)
    try {
      const res = await loyaltyPortal.listNotifications(tenant)
      setItems(res.data.items)
      setUnread(res.data.unread)
    } finally {
      setLoading(false)
    }
  }, [tenant])

  useEffect(() => {
    void refreshUnread()
    const timer = window.setInterval(() => void refreshUnread(), 30_000)
    return () => window.clearInterval(timer)
  }, [refreshUnread])

  useEffect(() => {
    if (isOpen) void loadNotifications()
  }, [isOpen, loadNotifications])

  useEffect(() => {
    if (!isOpen) return
    const handler = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    window.addEventListener('mousedown', handler)
    return () => window.removeEventListener('mousedown', handler)
  }, [isOpen])

  async function markRead(id: string) {
    await loyaltyPortal.markNotificationRead(tenant, id)
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)))
    setUnread((n) => Math.max(0, n - 1))
  }

  async function markAllRead() {
    await loyaltyPortal.markAllNotificationsRead(tenant)
    setItems((prev) => prev.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() })))
    setUnread(0)
  }

  if (!authed) return null

  return (
    <div className="relative ml-auto" ref={popoverRef}>
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="relative rounded-lg p-2 text-white/90 transition-colors hover:bg-white/10"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 ? (
          <span className="absolute -right-0.5 -top-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {unread > 99 ? '99+' : unread}
          </span>
        ) : null}
      </button>

      {isOpen ? (
        <div className="absolute right-0 z-50 mt-2 flex max-h-[24rem] w-80 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl">
          <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 className="text-sm font-bold text-slate-900">Notifications</h3>
            <button
              type="button"
              onClick={() => void markAllRead()}
              disabled={unread === 0}
              className="text-xs font-semibold text-[var(--tenant-primary)] disabled:cursor-not-allowed disabled:text-slate-300"
            >
              Mark all read
            </button>
          </header>

          <div className="flex-1 overflow-y-auto">
            {loading && items.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-slate-400">Loading…</div>
            ) : null}
            {!loading && items.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-slate-400">You&apos;re all caught up.</div>
            ) : null}
            <ul className="divide-y divide-slate-100">
              {items.map((n) => {
                const unreadRow = !n.read_at
                const href = walletPath(tenant, n.link)
                const row = (
                  <div className="group flex cursor-pointer items-start gap-3 px-4 py-3 hover:bg-slate-50">
                    <div
                      className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${
                        unreadRow ? 'bg-[var(--tenant-primary)]' : 'bg-transparent'
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className={`text-sm leading-snug ${unreadRow ? 'font-semibold text-slate-900' : 'text-slate-700'}`}>
                        {n.title}
                      </p>
                      {n.body ? <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.body}</p> : null}
                      <p className="mt-1 text-[10px] text-slate-400">{timeAgo(n.created_at)}</p>
                    </div>
                    {unreadRow ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          void markRead(n.id)
                        }}
                        className="rounded p-1 text-slate-400 opacity-0 transition-opacity hover:bg-emerald-50 hover:text-emerald-600 group-hover:opacity-100"
                        aria-label="Mark read"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                    ) : null}
                  </div>
                )
                return (
                  <li key={n.id}>
                    {href ? (
                      <Link
                        href={href}
                        onClick={() => {
                          if (unreadRow) void markRead(n.id)
                          setIsOpen(false)
                        }}
                      >
                        {row}
                      </Link>
                    ) : (
                      <div
                        onClick={() => {
                          if (unreadRow) void markRead(n.id)
                        }}
                      >
                        {row}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  )
}
