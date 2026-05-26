'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { BellRing, Check, Download, ExternalLink, Settings, X } from 'lucide-react'
import Link from 'next/link'
import { toast } from 'sonner'
import { notifications } from '@/lib/api-client'
import { enablePushAutomatically } from '@/lib/pwa/push-subscribe'

interface NotificationItem {
  id: string
  kind: string
  title: string
  body: string | null
  link: string | null
  read_at: string | null
  created_at: string
}

interface Preference {
  kind: string
  label: string
  in_app_enabled: boolean
  push_enabled: boolean
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function NotificationsPage() {
  const qc = useQueryClient()
  const feed = useQuery({
    queryKey: ['notifications', 'centre'],
    queryFn: () => notifications.list({ page: 1, page_size: 50 }).then((r) => r.data),
  })
  const prefs = useQuery<Preference[]>({
    queryKey: ['notifications', 'preferences'],
    queryFn: () => notifications.listPreferences().then((r) => r.data),
  })

  const markRead = useMutation({
    mutationFn: (id: string) => notifications.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
  const archive = useMutation({
    mutationFn: (id: string) => notifications.archive(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
  const savePrefs = useMutation({
    mutationFn: (items: Preference[]) =>
      notifications.updatePreferences(
        items.map((pref) => ({
          kind: pref.kind,
          in_app_enabled: pref.in_app_enabled,
          push_enabled: pref.push_enabled,
        })),
      ),
    onSuccess: () => {
      toast.success('Notification preferences saved')
      qc.invalidateQueries({ queryKey: ['notifications', 'preferences'] })
    },
    onError: () => toast.error('Could not save notification preferences'),
  })

  useEffect(() => {
    void enablePushAutomatically({ silent: true }).then((res) => {
      if (res.ok) toast.success(res.message)
    })
  }, [])

  const enablePush = async () => {
    const res = await enablePushAutomatically({ force: true })
    if (res.ok) toast.success(res.message)
    else toast.warning(res.message)
  }

  const prefItems = prefs.data ?? []
  const feedItems = (feed.data?.items ?? []) as NotificationItem[]

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <BellRing className="h-6 w-6 text-brand-teal-500" /> Notifications
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Review your in-app updates. Push alerts are enabled automatically — get pinged when a new lead arrives or a booking is due.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void enablePush()}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
        >
          <Download className="h-4 w-4" />
          Enable this device
        </button>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1fr,380px]">
        <div className="overflow-hidden rounded-xl border bg-card">
          <div className="border-b px-4 py-3">
            <h2 className="font-semibold">Notification centre</h2>
            <p className="text-xs text-muted-foreground">{feed.data?.unread ?? 0} unread</p>
          </div>
          {feed.isLoading ? (
            <div className="p-8 text-center text-sm text-muted-foreground">Loading notifications...</div>
          ) : feedItems.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">You are all caught up.</div>
          ) : (
            <ul className="divide-y">
              {feedItems.map((item) => (
                <li key={item.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <span className={`mt-2 h-2 w-2 rounded-full ${item.read_at ? 'bg-transparent' : 'bg-brand-teal-500'}`} />
                    <div className="min-w-0 flex-1">
                      <p className={`text-sm ${item.read_at ? 'text-muted-foreground' : 'font-semibold text-foreground'}`}>
                        {item.title}
                      </p>
                      {item.body && <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>}
                      <p className="mt-2 text-[11px] text-muted-foreground">
                        {item.kind} · {timeLabel(item.created_at)}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-1">
                      {item.link && (
                        <Link
                          href={item.link}
                          className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                          title="Open"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                      )}
                      {!item.read_at && (
                        <button
                          type="button"
                          onClick={() => markRead.mutate(item.id)}
                          className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-emerald-600"
                          title="Mark read"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => archive.mutate(item.id)}
                        className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-destructive"
                        title="Archive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <aside className="rounded-xl border bg-card">
          <div className="border-b px-4 py-3">
            <h2 className="flex items-center gap-2 font-semibold">
              <Settings className="h-4 w-4" /> Alert preferences
            </h2>
            <p className="text-xs text-muted-foreground">Push text stays privacy-safe on lock screens.</p>
          </div>
          <div className="divide-y">
            {prefItems.map((pref, index) => (
              <label key={pref.kind} className="flex cursor-pointer items-center justify-between gap-3 px-4 py-3">
                <span>
                  <span className="block text-sm font-medium">{pref.label}</span>
                  <span className="block text-[11px] text-muted-foreground">{pref.kind}</span>
                </span>
                <input
                  type="checkbox"
                  checked={pref.push_enabled}
                  onChange={(event) => {
                    const next = [...prefItems]
                    next[index] = { ...pref, push_enabled: event.target.checked }
                    qc.setQueryData(['notifications', 'preferences'], next)
                  }}
                  className="h-4 w-4 rounded border-input text-brand-forest-700"
                />
              </label>
            ))}
          </div>
          <div className="border-t p-4">
            <button
              type="button"
              onClick={() => savePrefs.mutate(prefItems)}
              disabled={savePrefs.isPending || prefItems.length === 0}
              className="w-full rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-60"
            >
              {savePrefs.isPending ? 'Saving...' : 'Save preferences'}
            </button>
          </div>
        </aside>
      </section>
    </div>
  )
}
