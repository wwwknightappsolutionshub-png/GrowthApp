'use client'

import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CalendarDays, Send } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

interface ScheduledItem {
  draft_id: string
  platform: string
  scheduled_time: string
  status: 'SCHEDULED' | 'PUBLISHED' | 'ERROR'
}

const PLATFORMS = ['FB', 'IG', 'TIKTOK', 'TWITTER']

export default function CalendarPage() {
  const [draftId, setDraftId] = useState('')
  const [platform, setPlatform] = useState('FB')
  const [time, setTime] = useState('')
  const [items, setItems] = useState<ScheduledItem[]>([])

  const scheduleMut = useMutation({
    mutationFn: () =>
      social.schedule({
        draft_id: draftId,
        platform,
        scheduled_time: time || undefined,
      }),
    onSuccess: (res) => {
      const scheduled_time =
        res.data?.scheduled_time || time || new Date(Date.now() + 2 * 3600_000).toISOString()
      setItems((prev) => [
        { draft_id: draftId, platform, scheduled_time, status: 'SCHEDULED' },
        ...prev,
      ])
      setDraftId('')
      setTime('')
      toast.success(`Queued for ${platform} at ${new Date(scheduled_time).toLocaleString()}`)
    },
    onError: () => toast.error('Failed to schedule'),
  })

  const publishMut = useMutation({
    mutationFn: (i: ScheduledItem) =>
      social.publish({ draft_id: i.draft_id, platform: i.platform }),
    onSuccess: (res, variables) => {
      const ok = res.data?.ok
      setItems((prev) =>
        prev.map((p) =>
          p.draft_id === variables.draft_id && p.platform === variables.platform
            ? { ...p, status: ok ? 'PUBLISHED' : 'ERROR' }
            : p,
        ),
      )
      toast[ok ? 'success' : 'error'](ok ? 'Published' : 'Publish failed')
    },
    onError: () => toast.error('Failed to publish'),
  })

  const grouped = useMemo(() => {
    const map = new Map<string, ScheduledItem[]>()
    for (const it of items) {
      const d = new Date(it.scheduled_time)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      map.set(key, [...(map.get(key) ?? []), it])
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [items])

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <CalendarDays className="h-6 w-6 text-primary" /> Scheduling Calendar
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Queue approved drafts for specific platforms and times. Empty time defaults to your
          next preferred slot.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-1">Draft ID</label>
          <input
            value={draftId}
            onChange={(e) => setDraftId(e.target.value)}
            placeholder="8e6b2a3f-…"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Platform</label>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          >
            {PLATFORMS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Scheduled time</label>
          <input
            type="datetime-local"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
        </div>
        <div className="md:col-span-4">
          <button
            onClick={() => {
              if (!draftId) return toast.error('Add a draft ID')
              scheduleMut.mutate()
            }}
            disabled={scheduleMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            <CalendarDays className="h-4 w-4" />
            {scheduleMut.isPending ? 'Scheduling…' : 'Add to calendar'}
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Upcoming schedule</h2>
        {grouped.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-8 text-center text-sm text-muted-foreground">
            Nothing scheduled yet.
          </div>
        ) : (
          <div className="space-y-4">
            {grouped.map(([day, list]) => (
              <div key={day} className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="bg-muted/40 px-4 py-2 text-xs font-semibold text-muted-foreground border-b border-border">
                  {new Date(day).toLocaleDateString(undefined, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>
                <div className="divide-y divide-border">
                  {list.map((it, idx) => (
                    <div
                      key={`${it.draft_id}-${idx}`}
                      className="flex items-center justify-between px-4 py-3"
                    >
                      <div>
                        <div className="text-sm font-medium">
                          {new Date(it.scheduled_time).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}{' '}
                          •{' '}
                          <span className="text-primary">{it.platform}</span>
                        </div>
                        <div className="text-xs font-mono text-muted-foreground">
                          {it.draft_id.slice(0, 8)}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            it.status === 'PUBLISHED'
                              ? 'bg-green-100 text-green-700'
                              : it.status === 'ERROR'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {it.status}
                        </span>
                        {it.status === 'SCHEDULED' && (
                          <button
                            onClick={() => publishMut.mutate(it)}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 text-xs font-semibold"
                          >
                            <Send className="h-3.5 w-3.5" /> Publish now
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
