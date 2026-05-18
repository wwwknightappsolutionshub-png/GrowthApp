'use client'

import { useEffect, useMemo, useState } from 'react'
import type React from 'react'
import { Loader2, RotateCcw, Save, Sparkles, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { admin } from '@/lib/api-client'
import { ADAPTIVE_NICHES, type AdaptiveGoal, type AdaptiveNicheConfig } from '@/lib/adaptive-ui-config'
import { cn } from '@/lib/utils'

type SavedAdaptivePage = {
  id: string
  niche_id: string
  label: string
  data: AdaptiveNicheConfig
  is_published: boolean
  updated_at: string
}

const input =
  'w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-600 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/30'
const label = 'mb-1 block text-xs font-medium text-gray-400'
const goals: AdaptiveGoal[] = ['grow', 'automate', 'reduce_workload']
const firstAdaptiveNiche = ADAPTIVE_NICHES[0] as AdaptiveNicheConfig

function cloneNiche(niche: AdaptiveNicheConfig): AdaptiveNicheConfig {
  return JSON.parse(JSON.stringify(niche)) as AdaptiveNicheConfig
}

function emptySavedMap(rows: SavedAdaptivePage[]) {
  return new Map(rows.map((row) => [row.niche_id, row]))
}

export default function AdaptivePagesAdminPage() {
  const [savedPages, setSavedPages] = useState<SavedAdaptivePage[]>([])
  const [selectedId, setSelectedId] = useState(firstAdaptiveNiche.id)
  const [draft, setDraft] = useState<AdaptiveNicheConfig>(() => cloneNiche(firstAdaptiveNiche))
  const [isPublished, setIsPublished] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const savedMap = useMemo(() => emptySavedMap(savedPages), [savedPages])
  const selectedDefault = ADAPTIVE_NICHES.find((niche) => niche.id === selectedId) ?? ADAPTIVE_NICHES[0]
  const selectedSaved = savedMap.get(selectedId)

  useEffect(() => {
    void refresh()
  }, [])

  useEffect(() => {
    if (!selectedDefault) return
    const saved = savedMap.get(selectedId)
    setDraft(cloneNiche(saved?.data ?? selectedDefault))
    setIsPublished(saved?.is_published ?? true)
  }, [selectedDefault, selectedId, savedMap])

  async function refresh() {
    setLoading(true)
    try {
      const res = await admin.listAdaptivePages()
      setSavedPages(res.data as SavedAdaptivePage[])
    } catch (err) {
      toast.error('Failed to load adaptive pages')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function patch(partial: Partial<AdaptiveNicheConfig>) {
    setDraft((current) => ({ ...current, ...partial }))
  }

  async function save() {
    setSaving(true)
    try {
      await admin.upsertAdaptivePage({
        niche_id: draft.id,
        label: draft.label,
        data: draft as unknown as Record<string, unknown>,
        is_published: isPublished,
      })
      toast.success('Adaptive page saved')
      await refresh()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not save adaptive page')
    } finally {
      setSaving(false)
    }
  }

  async function removeOverride() {
    if (!selectedSaved) return
    setDeleting(true)
    try {
      await admin.deleteAdaptivePage(selectedId)
      toast.success('Adaptive page reset to static fallback')
      await refresh()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not reset adaptive page')
    } finally {
      setDeleting(false)
    }
  }

  if (!selectedDefault) {
    return <p className="text-sm text-gray-400">No adaptive page defaults are configured.</p>
  }

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Adaptive Landing Pages</h1>
          <p className="mt-1 text-sm text-gray-400">
            Edit the personalized first-visit pages shown after visitors choose their business industry.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setDraft(cloneNiche(selectedDefault))
              setIsPublished(true)
            }}
            className="inline-flex items-center gap-2 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            <RotateCcw className="h-4 w-4" />
            Load fallback
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => void save()}
            className="inline-flex items-center gap-2 rounded-md bg-amber-500 px-3.5 py-2 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save page
          </button>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[300px,1fr]">
        <aside className="rounded-lg border border-gray-800 bg-gray-900/60 p-3">
          <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-500">
            Business industries
          </p>
          {loading && <p className="px-2 py-3 text-xs text-gray-500">Loading saved edits...</p>}
          <ul className="space-y-1">
            {ADAPTIVE_NICHES.map((niche) => {
              const saved = savedMap.get(niche.id)
              return (
                <li key={niche.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(niche.id)}
                    className={cn(
                      'flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors',
                      selectedId === niche.id
                        ? 'bg-amber-500/10 text-amber-100 ring-1 ring-amber-500/30'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                    )}
                  >
                    <span className="truncate">{niche.label}</span>
                    <span
                      className={cn(
                        'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold',
                        saved
                          ? saved.is_published
                            ? 'bg-emerald-500/15 text-emerald-300'
                            : 'bg-gray-700 text-gray-300'
                          : 'bg-gray-800 text-gray-500',
                      )}
                    >
                      {saved ? (saved.is_published ? 'Live' : 'Draft') : 'Fallback'}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </aside>

        <section className="space-y-5 rounded-lg border border-gray-800 bg-gray-900/40 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-gray-800 pb-4">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-200">
                <Sparkles className="h-3 w-3" />
                {selectedSaved ? 'CMS override' : 'Static fallback'}
              </p>
              <h2 className="mt-3 text-lg font-semibold text-white">{draft.label}</h2>
              <p className="mt-1 font-mono text-[10px] text-gray-500">
                niche_id: {draft.id}
                {selectedSaved ? ` · updated ${new Date(selectedSaved.updated_at).toLocaleString('en-GB')}` : ''}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-2 text-xs text-gray-400">
                <input
                  type="checkbox"
                  checked={isPublished}
                  onChange={(event) => setIsPublished(event.target.checked)}
                  className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-amber-500 focus:ring-amber-500"
                />
                Published
              </label>
              {selectedSaved && (
                <button
                  type="button"
                  disabled={deleting}
                  onClick={() => void removeOverride()}
                  className="inline-flex items-center gap-2 rounded-md border border-rose-500/30 px-3 py-2 text-sm font-medium text-rose-200 hover:bg-rose-500/10 disabled:opacity-50"
                >
                  {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                  Reset override
                </button>
              )}
            </div>
          </div>

          <AdaptivePageForm draft={draft} patch={patch} />
        </section>
      </div>
    </div>
  )
}

function Field({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className={label}>{title}</span>
      {children}
    </label>
  )
}

function AdaptivePageForm({
  draft,
  patch,
}: {
  draft: AdaptiveNicheConfig
  patch: (partial: Partial<AdaptiveNicheConfig>) => void
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field title="Business industry label">
          <input className={input} value={draft.label} onChange={(e) => patch({ label: e.target.value })} />
        </Field>
        <Field title="Hero eyebrow">
          <input
            className={input}
            value={draft.hero.eyebrow}
            onChange={(e) => patch({ hero: { ...draft.hero, eyebrow: e.target.value } })}
          />
        </Field>
      </div>

      <Field title="Hero headline">
        <input
          className={input}
          value={draft.hero.headline}
          onChange={(e) => patch({ hero: { ...draft.hero, headline: e.target.value } })}
        />
      </Field>

      <Field title="Hero subheadline">
        <textarea
          className={cn(input, 'min-h-[90px] resize-y')}
          value={draft.hero.subheadline}
          onChange={(e) => patch({ hero: { ...draft.hero, subheadline: e.target.value } })}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field title="Primary CTA">
          <input
            className={input}
            value={draft.hero.primaryCta}
            onChange={(e) => patch({ hero: { ...draft.hero, primaryCta: e.target.value } })}
          />
        </Field>
        <Field title="Secondary CTA">
          <input
            className={input}
            value={draft.hero.secondaryCta}
            onChange={(e) => patch({ hero: { ...draft.hero, secondaryCta: e.target.value } })}
          />
        </Field>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr,220px]">
        <div className="space-y-4">
          <Field title="Hero image URL">
            <input
              className={input}
              value={draft.hero.image}
              onChange={(e) => patch({ hero: { ...draft.hero, image: e.target.value } })}
            />
          </Field>
          <Field title="Hero image alt text">
            <input
              className={input}
              value={draft.hero.imageAlt}
              onChange={(e) => patch({ hero: { ...draft.hero, imageAlt: e.target.value } })}
            />
          </Field>
        </div>
        <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-950">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={draft.hero.image} alt={draft.hero.imageAlt} className="h-36 w-full object-cover" />
          <p className="p-3 text-[11px] text-gray-500">Preview</p>
        </div>
      </div>

      <div>
        <p className={label}>Pain points</p>
        <div className="space-y-3">
          {draft.painPoints.map((painPoint, index) => (
            <div key={painPoint.id} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field title={`Pain point ${index + 1} label`}>
                  <input
                    className={input}
                    value={painPoint.label}
                    onChange={(e) => {
                      const next = [...draft.painPoints]
                      next[index] = { ...next[index], label: e.target.value }
                      patch({ painPoints: next })
                    }}
                  />
                </Field>
                <Field title="Description">
                  <input
                    className={input}
                    value={painPoint.description}
                    onChange={(e) => {
                      const next = [...draft.painPoints]
                      next[index] = { ...next[index], description: e.target.value }
                      patch({ painPoints: next })
                    }}
                  />
                </Field>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className={label}>Goal copy</p>
        <div className="grid gap-3 lg:grid-cols-3">
          {goals.map((goal) => (
            <div key={goal} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4">
              <Field title={`${goal} title`}>
                <input
                  className={input}
                  value={draft.goalBlocks[goal].title}
                  onChange={(e) =>
                    patch({
                      goalBlocks: {
                        ...draft.goalBlocks,
                        [goal]: { ...draft.goalBlocks[goal], title: e.target.value },
                      },
                    })
                  }
                />
              </Field>
              <Field title="Body">
                <textarea
                  className={cn(input, 'mt-3 min-h-[96px] resize-y')}
                  value={draft.goalBlocks[goal].body}
                  onChange={(e) =>
                    patch({
                      goalBlocks: {
                        ...draft.goalBlocks,
                        [goal]: { ...draft.goalBlocks[goal], body: e.target.value },
                      },
                    })
                  }
                />
              </Field>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field title="Testimonial quote">
          <textarea
            className={cn(input, 'min-h-[100px] resize-y')}
            value={draft.testimonials[0]?.quote ?? ''}
            onChange={(e) => {
              const first = draft.testimonials[0] ?? { name: '', role: '' }
              patch({ testimonials: [{ ...first, quote: e.target.value }] })
            }}
          />
        </Field>
        <div className="space-y-4">
          <Field title="Testimonial name">
            <input
              className={input}
              value={draft.testimonials[0]?.name ?? ''}
              onChange={(e) => {
                const first = draft.testimonials[0] ?? { quote: '', role: '' }
                patch({ testimonials: [{ ...first, name: e.target.value }] })
              }}
            />
          </Field>
          <Field title="Testimonial role">
            <input
              className={input}
              value={draft.testimonials[0]?.role ?? ''}
              onChange={(e) => {
                const first = draft.testimonials[0] ?? { quote: '', name: '' }
                patch({ testimonials: [{ ...first, role: e.target.value }] })
              }}
            />
          </Field>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field title="CTA text">
          <input className={input} value={draft.ctaText} onChange={(e) => patch({ ctaText: e.target.value })} />
        </Field>
        <Field title="Why block title">
          <input
            className={input}
            value={draft.whyBlock.title}
            onChange={(e) => patch({ whyBlock: { ...draft.whyBlock, title: e.target.value } })}
          />
        </Field>
      </div>
      <Field title="Why block body">
        <textarea
          className={cn(input, 'min-h-[100px] resize-y')}
          value={draft.whyBlock.body}
          onChange={(e) => patch({ whyBlock: { ...draft.whyBlock, body: e.target.value } })}
        />
      </Field>
    </div>
  )
}
