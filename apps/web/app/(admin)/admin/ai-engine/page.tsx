'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Brain, Save, FlaskConical, Shield, GitMerge, Lock } from 'lucide-react'
import { adminApi, type AIEngineConfig } from '@/lib/api-client'

type Tab = 'prompt' | 'scoring' | 'dedupe' | 'fraud'

const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: 'prompt', label: 'Extraction Prompt', icon: Lock },
  { key: 'scoring', label: 'Scoring Engine', icon: Brain },
  { key: 'dedupe', label: 'Duplicate Suppression', icon: GitMerge },
  { key: 'fraud', label: 'Fraud / Spam Rules', icon: Shield },
]

export default function AIEnginePage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('prompt')
  const [toast, setToast] = useState('')
  const [testLead, setTestLead] = useState({ name: '', email: '', phone: '', business: '', location: '', service_need: '', intent_level: 'high', urgency: 'immediate' })
  const [testResult, setTestResult] = useState<null | { ai_score: number }>(null)

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: prompt } = useQuery({ queryKey: ['admin', 'ai-engine', 'prompt'], queryFn: () => adminApi.getExtractionPrompt().then(r => r.data as { prompt: string; readonly: boolean }) })
  const { data: scoring, isLoading: scoringLoading } = useQuery({ queryKey: ['admin', 'ai-engine', 'scoring'], queryFn: () => adminApi.getScoringConfig().then(r => r.data) })
  const { data: dedupe } = useQuery({ queryKey: ['admin', 'ai-engine', 'dedupe'], queryFn: () => adminApi.getDedupeConfig().then(r => r.data as Record<string, unknown>) })
  const { data: fraud } = useQuery({ queryKey: ['admin', 'ai-engine', 'fraud'], queryFn: () => adminApi.getFraudConfig().then(r => r.data as Record<string, unknown>) })

  const [scoringForm, setScoringForm] = useState<AIEngineConfig | null>(null)
  const [dedupeForm, setDedupeForm] = useState<Record<string, unknown> | null>(null)
  const [fraudForm, setFraudForm] = useState<Record<string, unknown> | null>(null)

  const scoringMut = useMutation({
    mutationFn: (body: AIEngineConfig) => adminApi.updateScoringConfig(body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ai-engine', 'scoring'] }); showToast('Scoring config saved') },
  })
  const dedupeMut = useMutation({
    mutationFn: (body: object) => adminApi.updateDedupeConfig(body),
    onSuccess: () => { showToast('Dedupe config saved') },
  })
  const fraudMut = useMutation({
    mutationFn: (body: object) => adminApi.updateFraudConfig(body),
    onSuccess: () => { showToast('Fraud config saved') },
  })
  const testMut = useMutation({
    mutationFn: () => adminApi.testScore(testLead),
    onSuccess: (r) => setTestResult(r.data as { ai_score: number }),
  })

  const scoringData = scoringForm ?? scoring
  const dedupeData = dedupeForm ?? dedupe
  const fraudData = fraudForm ?? fraud

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Brain className="h-6 w-6 text-amber-400" /> AI Lead Intelligence Engine</h1>
        <p className="text-sm text-gray-400 mt-1">Configure extraction rules, scoring weights, deduplication and fraud prevention</p>
      </div>

      <div className="mb-6 flex flex-wrap gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${tab === t.key ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'prompt' && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <div className="flex items-center gap-2 mb-3">
            <Lock className="h-4 w-4 text-amber-400" />
            <h2 className="font-semibold">Extraction Prompt (Read-Only)</h2>
            <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-400">Ruleset 1–4</span>
          </div>
          <p className="text-xs text-gray-400 mb-3">This is the verbatim Lead Intelligence Engine prompt. It cannot be edited via the UI.</p>
          <pre className="text-xs text-green-300 bg-gray-950 rounded-lg p-4 overflow-x-auto max-h-96 whitespace-pre-wrap border border-gray-700">
            {prompt?.prompt ?? 'Loading…'}
          </pre>
        </div>
      )}

      {tab === 'scoring' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <h2 className="mb-4 font-semibold">Scoring Weights</h2>
            {scoringLoading ? <div className="text-gray-400">Loading…</div> : scoringData && (
              <div className="space-y-3">
                {Object.entries(scoringData).map(([key, val]) => (
                  <div key={key}>
                    <label className="mb-1 block text-xs text-gray-400 capitalize">{key.replace(/_/g, ' ')}</label>
                    <input type="number" min={0} max={200}
                      value={Number(val)}
                      onChange={e => setScoringForm(f => ({ ...(f ?? (scoringData as AIEngineConfig)), [key]: Number(e.target.value) }))}
                      className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
                  </div>
                ))}
                <button onClick={() => scoringMut.mutate(scoringData as AIEngineConfig)} disabled={scoringMut.isPending}
                  className="mt-2 flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">
                  <Save className="h-4 w-4" /> {scoringMut.isPending ? 'Saving…' : 'Save Weights'}
                </button>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <h2 className="mb-4 font-semibold flex items-center gap-2"><FlaskConical className="h-4 w-4 text-amber-400" /> Test Score</h2>
            <div className="space-y-2">
              {Object.entries(testLead).map(([key, val]) => (
                <div key={key}>
                  <label className="mb-0.5 block text-xs text-gray-400 capitalize">{key.replace(/_/g, ' ')}</label>
                  <input value={val} onChange={e => setTestLead(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-white outline-none focus:border-amber-500" />
                </div>
              ))}
            </div>
            <button onClick={() => testMut.mutate()} disabled={testMut.isPending}
              className="mt-3 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
              Calculate Score
            </button>
            {testResult && (
              <div className="mt-3 rounded-lg bg-gray-800 p-3">
                <p className="text-sm text-gray-300">AI Score: <span className="text-2xl font-bold text-amber-400">{testResult.ai_score}</span> / 100</p>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'dedupe' && dedupeData && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 max-w-lg">
          <h2 className="mb-4 font-semibold">Duplicate Suppression</h2>
          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={Boolean((dedupeForm ?? dedupeData).enabled)} onChange={e => setDedupeForm(f => ({ ...(f ?? dedupeData), enabled: e.target.checked }))} />
              <span className="text-sm text-gray-300">Enabled</span>
            </label>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Window (days)</label>
              <input type="number" min={1} value={Number((dedupeForm ?? dedupeData).window_days ?? 30)}
                onChange={e => setDedupeForm(f => ({ ...(f ?? dedupeData), window_days: Number(e.target.value) }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Similarity Threshold (0–1)</label>
              <input type="number" step={0.05} min={0} max={1} value={Number((dedupeForm ?? dedupeData).similarity_threshold ?? 0.85)}
                onChange={e => setDedupeForm(f => ({ ...(f ?? dedupeData), similarity_threshold: Number(e.target.value) }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
            </div>
          </div>
          <button onClick={() => dedupeMut.mutate(dedupeForm ?? dedupeData)} disabled={dedupeMut.isPending}
            className="mt-4 flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
            <Save className="h-4 w-4" /> {dedupeMut.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      )}

      {tab === 'fraud' && fraudData && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 max-w-lg">
          <h2 className="mb-4 font-semibold">Fraud / Spam Rules</h2>
          <div className="space-y-3">
            {[['enabled', 'Enabled'], ['block_disposable_emails', 'Block Disposable Emails']].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={Boolean((fraudForm ?? fraudData)[key])}
                  onChange={e => setFraudForm(f => ({ ...(f ?? fraudData), [key]: e.target.checked }))} />
                <span className="text-sm text-gray-300">{label}</span>
              </label>
            ))}
            <div>
              <label className="mb-1 block text-xs text-gray-400">Minimum Score Threshold</label>
              <input type="number" min={0} max={100} value={Number((fraudForm ?? fraudData).min_score_threshold ?? 10)}
                onChange={e => setFraudForm(f => ({ ...(f ?? fraudData), min_score_threshold: Number(e.target.value) }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Block Keywords (comma-separated)</label>
              <input value={((fraudForm ?? fraudData).block_keywords as string[] ?? []).join(', ')}
                onChange={e => setFraudForm(f => ({ ...(f ?? fraudData), block_keywords: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
            </div>
          </div>
          <button onClick={() => fraudMut.mutate(fraudForm ?? fraudData)} disabled={fraudMut.isPending}
            className="mt-4 flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
            <Save className="h-4 w-4" /> {fraudMut.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      )}
    </div>
  )
}
