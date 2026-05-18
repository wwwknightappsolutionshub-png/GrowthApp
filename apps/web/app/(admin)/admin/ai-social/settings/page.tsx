'use client'

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Settings2 } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface AiConfig {
  model: string
  max_drafts_per_run: number
  auto_approve: boolean
  default_tone: string
  enabled_platforms: string[]
}

const ALL_PLATFORMS = ['FB', 'IG', 'TIKTOK', 'TWITTER']

export default function AiSocialSettingsPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState<AiConfig | null>(null)
  const [toast, setToast] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'social', 'ai-config'],
    queryFn: () => adminApi.socialGetAiConfig().then((r) => r.data),
  })

  useEffect(() => {
    if (data?.config) setForm(data.config as AiConfig)
  }, [data])

  const saveMut = useMutation({
    mutationFn: (body: AiConfig) => adminApi.socialSetAiConfig(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'social', 'ai-config'] })
      setToast('Settings saved')
      setTimeout(() => setToast(''), 2500)
    },
  })

  function togglePlatform(p: string) {
    if (!form) return
    const set = new Set(form.enabled_platforms)
    if (set.has(p)) set.delete(p)
    else set.add(p)
    setForm({ ...form, enabled_platforms: Array.from(set) })
  }

  return (
    <div className="text-white">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium shadow-lg">
          {toast}
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings2 className="h-6 w-6 text-amber-400" /> Global AI Settings
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Platform-wide configuration for the AI Social content generator.
        </p>
      </div>

      {isLoading || !form ? (
        <div className="text-gray-400">Loading…</div>
      ) : (
        <div className="max-w-2xl space-y-5 rounded-xl border border-gray-800 bg-gray-900 p-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Model</label>
            <input
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
              className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Max drafts per run
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={form.max_drafts_per_run}
              onChange={(e) =>
                setForm({ ...form, max_drafts_per_run: parseInt(e.target.value || '1', 10) })
              }
              className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Default tone</label>
            <input
              value={form.default_tone}
              onChange={(e) => setForm({ ...form, default_tone: e.target.value })}
              className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Enabled platforms
            </label>
            <div className="flex flex-wrap gap-2">
              {ALL_PLATFORMS.map((p) => {
                const on = form.enabled_platforms.includes(p)
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => togglePlatform(p)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${
                      on
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={form.auto_approve}
              onChange={(e) => setForm({ ...form, auto_approve: e.target.checked })}
            />
            Auto-approve drafts (skip approval queue)
          </label>

          <button
            onClick={() => saveMut.mutate(form)}
            disabled={saveMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            {saveMut.isPending ? 'Saving…' : 'Save settings'}
          </button>
        </div>
      )}
    </div>
  )
}
