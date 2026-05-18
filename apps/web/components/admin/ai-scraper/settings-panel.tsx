'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Save } from 'lucide-react'
import { toast } from 'sonner'

import { aiScraper, type AggressionLevel } from '@/lib/api-client'
import {
  buttonPrimaryClass,
  formatDate,
  inputClass,
  labelClass,
  SectionCard,
} from './shared'

const AGGRESSION_LEVELS: AggressionLevel[] = ['low', 'medium', 'high', 'extreme']

export function SettingsPanel() {
  const qc = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['ai-scraper', 'settings'],
    queryFn: () => aiScraper.getSettings().then((r) => r.data),
  })

  const [threadCount, setThreadCount] = useState<number>(4)
  const [mode, setMode] = useState<AggressionLevel>('low')

  useEffect(() => {
    if (data) {
      setThreadCount(data.thread_count)
      setMode(data.global_aggression_mode as AggressionLevel)
    }
  }, [data])

  const save = useMutation({
    mutationFn: () =>
      aiScraper.updateSettings({
        thread_count: threadCount,
        global_aggression_mode: mode,
      }),
    onSuccess: () => {
      toast.success('Settings saved')
      qc.invalidateQueries({ queryKey: ['ai-scraper', 'settings'] })
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to save settings'),
  })

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (threadCount < 1 || threadCount > 64) {
      toast.error('Thread count must be between 1 and 64')
      return
    }
    save.mutate()
  }

  return (
    <SectionCard
      title="Global settings"
      description="Platform-wide knobs that govern parallelism and default aggression."
    >
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Failed to load settings.
        </div>
      )}
      {isLoading && (
        <div className="h-24 animate-pulse rounded-lg bg-gray-800" />
      )}
      {!isLoading && data && (
        <form onSubmit={onSubmit} className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="thread-count">
                Parallel scraping threads
              </label>
              <input
                id="thread-count"
                type="number"
                min={1}
                max={64}
                className={inputClass}
                value={threadCount}
                onChange={(e) => setThreadCount(Number(e.target.value))}
              />
              <p className="mt-1 text-xs text-gray-500">
                Worker concurrency for scraper jobs (1-64).
              </p>
            </div>
            <div>
              <label className={labelClass} htmlFor="aggression-mode">
                Global aggression mode
              </label>
              <select
                id="aggression-mode"
                className={inputClass}
                value={mode}
                onChange={(e) => setMode(e.target.value as AggressionLevel)}
              >
                {AGGRESSION_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Applied as a default to tasks. Tasks may still override.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-gray-800 pt-4">
            <div className="text-xs text-gray-500">
              Last updated: {formatDate(data.updated_at)}
            </div>
            <button
              type="submit"
              className={buttonPrimaryClass}
              disabled={save.isPending}
            >
              <Save className="h-4 w-4" />
              Save settings
            </button>
          </div>
        </form>
      )}
    </SectionCard>
  )
}
