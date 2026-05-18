'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CalendarRange, Save } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export default function PreferencesPage() {
  const [postsPerWeek, setPostsPerWeek] = useState(3)
  const [days, setDays] = useState<string[]>(['Tue', 'Thu'])
  const [timeRange, setTimeRange] = useState('09:00-17:00')

  const saveMut = useMutation({
    mutationFn: () =>
      social.setPrefs({
        posts_per_week: postsPerWeek,
        preferred_days: days,
        preferred_time_range: timeRange,
      }),
    onSuccess: () => toast.success('Posting preferences saved'),
    onError: () => toast.error('Failed to save preferences'),
  })

  function toggleDay(d: string) {
    setDays((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]))
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <CalendarRange className="h-6 w-6 text-primary" /> Posting Preferences
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Tell the scheduler how often and when you want to post. The AI will pace its drafts
          around this cadence.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-6">
        <section>
          <h2 className="text-sm font-semibold mb-2 text-foreground">Posts per week</h2>
          <input
            type="range"
            min={1}
            max={14}
            value={postsPerWeek}
            onChange={(e) => setPostsPerWeek(parseInt(e.target.value, 10))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>1</span>
            <span className="font-bold text-primary text-base">{postsPerWeek}</span>
            <span>14</span>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold mb-2 text-foreground">Preferred days</h2>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((d) => {
              const on = days.includes(d)
              return (
                <button
                  key={d}
                  onClick={() => toggleDay(d)}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold border ${
                    on
                      ? 'bg-primary/10 text-primary border-primary/40'
                      : 'bg-card text-muted-foreground border-border hover:border-foreground/30'
                  }`}
                >
                  {d}
                </button>
              )
            })}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold mb-2 text-foreground">Preferred time range</h2>
          <input
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            placeholder="e.g. 09:00-17:00"
            className="w-full max-w-xs rounded-lg bg-background border border-border px-3 py-2 text-sm font-mono"
          />
          <p className="text-xs text-muted-foreground mt-1">
            24-hour format, ranges separated by a hyphen.
          </p>
        </section>

        <button
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Save className="h-4 w-4" />
          {saveMut.isPending ? 'Saving…' : 'Save preferences'}
        </button>
      </div>
    </div>
  )
}
