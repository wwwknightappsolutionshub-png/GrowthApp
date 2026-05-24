'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Copy, ExternalLink, Loader2, RefreshCw, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'

type BenefitRow = { title: string; body: string }

export function MembershipLandingEditor({ tenantSlug }: { tenantSlug?: string }) {
  const qc = useQueryClient()
  const landingQ = useQuery({
    queryKey: ['mr-landing'],
    queryFn: async () => (await membershipRewards.getLanding()).data,
  })

  const [title, setTitle] = useState('')
  const [meta, setMeta] = useState('')
  const [headline, setHeadline] = useState('')
  const [subheadline, setSubheadline] = useState('')
  const [ctaLabel, setCtaLabel] = useState('')
  const [ctaHref, setCtaHref] = useState('')
  const [benefits, setBenefits] = useState<BenefitRow[]>([])

  useEffect(() => {
    const d = landingQ.data
    if (!d) return
    setTitle(d.title)
    setMeta(d.meta_description ?? '')
    setHeadline(String((d.hero as { headline?: string })?.headline ?? ''))
    setSubheadline(String((d.hero as { subheadline?: string })?.subheadline ?? ''))
    setCtaLabel(d.cta_label)
    setCtaHref(d.cta_href ?? '')
    setBenefits(
      (d.benefits ?? []).map((b) => ({
        title: b.title ?? '',
        body: b.body ?? '',
      })),
    )
  }, [landingQ.data])

  const save = useMutation({
    mutationFn: () =>
      membershipRewards.updateLanding({
        title,
        meta_description: meta || null,
        hero: { headline, subheadline },
        benefits,
        cta_label: ctaLabel,
        cta_href: ctaHref || null,
        ...(landingQ.data?.published ? { published: true } : {}),
      }),
    onSuccess: () => {
      toast.success(
        landingQ.data?.published
          ? 'Live page updated — changes are visible now'
          : 'Landing saved',
      )
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
    },
    onError: () => toast.error('Could not save landing'),
  })

  const regenerate = useMutation({
    mutationFn: () => membershipRewards.regenerateLanding(),
    onSuccess: () => {
      toast.success('Landing regenerated from your plans')
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
    },
    onError: () => toast.error('Regenerate failed'),
  })

  const publish = useMutation({
    mutationFn: () => membershipRewards.publishLanding(),
    onSuccess: () => {
      toast.success('Landing published')
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-status'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-dashboard'] })
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Publish failed — add an active plan first'
      toast.error(String(msg))
    },
  })

  const copyUrl = (url: string) => {
    void navigator.clipboard.writeText(url)
    toast.success('Link copied')
  }

  const publicUrl =
    landingQ.data?.public_url ??
    (tenantSlug && typeof window !== 'undefined'
      ? `${window.location.origin}/p/${tenantSlug}/memberships`
      : null)

  if (landingQ.isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Public memberships page</h2>
          <p className="text-sm text-slate-400 mt-1">
            Auto-updates when you add plans. Live at{' '}
            <code className="text-brand-teal-300">/p/{tenantSlug ?? 'your-business'}/memberships</code>
            {tenantSlug ? (
              <>
                {' '}
                (alias{' '}
                <code className="text-brand-teal-300">/p/{tenantSlug}/loyalty</code>)
              </>
            ) : null}
          </p>
        </div>
        {landingQ.data?.auto_generated ? (
          <span className="text-xs rounded-full bg-brand-teal-600/20 text-brand-teal-200 px-2 py-1">
            Auto-generated
          </span>
        ) : (
          <span className="text-xs rounded-full bg-slate-600/30 text-slate-300 px-2 py-1">Customized</span>
        )}
      </div>

      {(landingQ.data?.plans?.length ?? 0) === 0 && (
        <p className="text-sm text-amber-200/90 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          Create at least one active membership plan — your landing page will auto-publish when the first plan is
          saved.
        </p>
      )}

      {publicUrl && landingQ.data?.published && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <a
            href={publicUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-brand-teal-300 hover:text-white"
          >
            {publicUrl} <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <button
            type="button"
            onClick={() => copyUrl(publicUrl)}
            className="inline-flex items-center gap-1 text-slate-400 hover:text-white"
          >
            <Copy className="w-3.5 h-3.5" /> Copy
          </button>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="text-xs text-slate-400">Page title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block md:col-span-2">
          <span className="text-xs text-slate-400">Meta description (SEO)</span>
          <textarea
            value={meta}
            onChange={(e) => setMeta(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-400">Hero headline</span>
          <input
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-400">Hero subheadline</span>
          <input
            value={subheadline}
            onChange={(e) => setSubheadline(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
        </label>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Benefits</span>
          <button
            type="button"
            onClick={() => setBenefits((b) => [...b, { title: '', body: '' }])}
            className="text-xs text-brand-teal-300 hover:text-brand-teal-200"
          >
            + Add row
          </button>
        </div>
        <div className="space-y-3">
          {benefits.map((row, i) => (
            <div key={i} className="grid gap-2 sm:grid-cols-2 rounded-lg border border-white/10 p-3">
              <input
                placeholder="Title"
                value={row.title}
                onChange={(e) => {
                  const next = [...benefits]
                  next[i] = { ...next[i], title: e.target.value }
                  setBenefits(next)
                }}
                className="rounded border border-white/10 bg-brand-forest-950 px-2 py-1.5 text-sm text-white"
              />
              <input
                placeholder="Description"
                value={row.body}
                onChange={(e) => {
                  const next = [...benefits]
                  next[i] = { ...next[i], body: e.target.value }
                  setBenefits(next)
                }}
                className="rounded border border-white/10 bg-brand-forest-950 px-2 py-1.5 text-sm text-white"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs text-slate-400">CTA button label</span>
          <input
            value={ctaLabel}
            onChange={(e) => setCtaLabel(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-400">CTA link</span>
          <input
            value={ctaHref}
            onChange={(e) => setCtaHref(e.target.value)}
            placeholder={landingQ.data?.booking_cta_url ?? '/book/your-slug'}
            className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          />
          {landingQ.data?.booking_cta_url && (
            <button
              type="button"
              onClick={() => setCtaHref(landingQ.data?.booking_cta_url ?? '')}
              className="mt-1 text-xs text-brand-teal-400 hover:underline"
            >
              Use booking page URL
            </button>
          )}
        </label>
      </div>

      {(landingQ.data?.tiers?.length ?? 0) > 0 && (
        <p className="text-xs text-slate-500">
          Loyalty tiers are edited under{' '}
          <a
            href="/dashboard/membership-rewards?section=loyalty"
            className="text-brand-teal-300 hover:underline"
          >
            Loyalty → tier settings
          </a>
          .
        </p>
      )}

      <div className="flex flex-wrap gap-3 pt-2 border-t border-white/10">
        <button
          type="button"
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className={
            landingQ.data?.published
              ? 'inline-flex items-center gap-2 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50'
              : 'rounded-lg border border-white/20 px-4 py-2 text-sm text-white hover:bg-white/5 disabled:opacity-50'
          }
        >
          {landingQ.data?.published ? 'Update & Save' : 'Save draft'}
        </button>
        <button
          type="button"
          onClick={() => regenerate.mutate()}
          disabled={regenerate.isPending}
          className="inline-flex items-center gap-2 rounded-lg border border-brand-teal-500/40 px-4 py-2 text-sm text-brand-teal-200 hover:bg-brand-teal-600/10"
        >
          <RefreshCw className={`w-4 h-4 ${regenerate.isPending ? 'animate-spin' : ''}`} />
          Regenerate from plans
        </button>
        <button
          type="button"
          onClick={() => publish.mutate()}
          disabled={publish.isPending}
          className={
            landingQ.data?.published
              ? 'hidden'
              : 'inline-flex items-center gap-2 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500'
          }
        >
          <Sparkles className="w-4 h-4" />
          Publish
        </button>
      </div>

      {landingQ.data?.published ? (
        <p className="text-xs text-emerald-300">Published — customers can view plans and submit interest.</p>
      ) : (
        <p className="text-xs text-slate-500">Draft only — not visible publicly until published.</p>
      )}
    </div>
  )
}
