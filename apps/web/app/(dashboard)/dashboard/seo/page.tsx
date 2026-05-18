'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle2, Loader2, Search, Sparkles, XCircle } from 'lucide-react'
import { ai } from '@/lib/api-client'

type SeoAudit = {
  score: number
  summary: string
  suggested_title: string
  suggested_description: string
  suggested_keywords: string[]
  gbp_recommendations: string[]
  issues: string[]
  provider: string
  model: string
}

export default function SeoPage() {
  const [pageUrl, setPageUrl] = useState('')
  const [title, setTitle] = useState('')
  const [meta, setMeta] = useState('')
  const [body, setBody] = useState('')
  const [keywords, setKeywords] = useState('')
  const [localArea, setLocalArea] = useState('')

  const mutation = useMutation<{ data: SeoAudit }, Error>({
    mutationFn: () =>
      ai.seoAudit({
        page_url: pageUrl,
        page_title: title,
        meta_description: meta,
        body_excerpt: body,
        target_keywords: keywords
          .split(',')
          .map((k) => k.trim())
          .filter(Boolean),
        local_area: localArea,
      }),
  })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Search className="w-6 h-6 text-blue-600" /> SEO Assistant
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste a page and get an AI-driven audit with title, meta, keyword and Google Business Profile suggestions.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-card p-5 space-y-4">
          <Field label="Page URL" value={pageUrl} onChange={setPageUrl} placeholder="https://..." />
          <Field
            label="Current title tag"
            value={title}
            onChange={setTitle}
            placeholder="Best Plumbers in Manchester | AcmePlumb"
          />
          <Field
            label="Current meta description"
            value={meta}
            onChange={setMeta}
            multiline
            rows={2}
          />
          <Field
            label="Target keywords (comma-separated)"
            value={keywords}
            onChange={setKeywords}
            placeholder="emergency plumber Manchester, boiler repair"
          />
          <Field
            label="Local area (for local SEO)"
            value={localArea}
            onChange={setLocalArea}
            placeholder="Manchester, UK"
          />
          <Field label="Body excerpt" value={body} onChange={setBody} multiline rows={6} />

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !pageUrl || !title}
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            Audit page
          </button>

          {mutation.isError && (
            <p className="text-xs text-red-600">
              {(mutation.error as Error)?.message || 'Audit failed'}
            </p>
          )}
        </section>

        <section className="space-y-4">
          {mutation.data ? (
            <AuditResults audit={mutation.data.data} />
          ) : (
            <div className="rounded-xl border bg-card p-12 text-center text-muted-foreground text-sm">
              Fill out the form and click <strong>Audit page</strong> for AI-driven recommendations.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function AuditResults({ audit }: { audit: SeoAudit }) {
  return (
    <>
      <div className="rounded-xl border bg-card p-5 flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">SEO Score</p>
          <p className="text-4xl font-bold">
            {audit.score}
            <span className="text-base font-normal text-gray-400">/100</span>
          </p>
        </div>
        <div className="w-32 h-32">
          <ScoreRing score={audit.score} />
        </div>
      </div>

      <Card title="Summary">
        <p className="text-sm leading-relaxed">{audit.summary}</p>
      </Card>

      <Card title="Suggested title tag">
        <p className="text-sm font-medium">{audit.suggested_title}</p>
        <p className="text-xs text-muted-foreground mt-1">{audit.suggested_title.length} characters</p>
      </Card>

      <Card title="Suggested meta description">
        <p className="text-sm">{audit.suggested_description}</p>
        <p className="text-xs text-muted-foreground mt-1">{audit.suggested_description.length} characters</p>
      </Card>

      {audit.suggested_keywords.length > 0 && (
        <Card title="Suggested keywords">
          <div className="flex flex-wrap gap-2">
            {audit.suggested_keywords.map((k) => (
              <span key={k} className="rounded-full bg-blue-50 text-blue-700 text-xs px-2.5 py-1">
                {k}
              </span>
            ))}
          </div>
        </Card>
      )}

      {audit.gbp_recommendations.length > 0 && (
        <Card title="Google Business Profile">
          <ul className="space-y-2 text-sm">
            {audit.gbp_recommendations.map((r, i) => (
              <li key={i} className="flex gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {audit.issues.length > 0 && (
        <Card title="Issues to fix">
          <ul className="space-y-2 text-sm">
            {audit.issues.map((r, i) => (
              <li key={i} className="flex gap-2">
                <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <p className="text-xs text-gray-400 text-right">
        Audited by {audit.provider}/{audit.model}
      </p>
    </>
  )
}

function ScoreRing({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score))
  const colour = clamped >= 75 ? '#16a34a' : clamped >= 50 ? '#f59e0b' : '#dc2626'
  const c = 2 * Math.PI * 42
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <circle cx="50" cy="50" r="42" stroke="#e5e7eb" strokeWidth="8" fill="none" />
      <circle
        cx="50"
        cy="50"
        r="42"
        stroke={colour}
        strokeWidth="8"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c - (clamped / 100) * c}
        transform="rotate(-90 50 50)"
      />
      <text
        x="50"
        y="55"
        textAnchor="middle"
        fontSize="22"
        fontWeight="700"
        fill={colour}
      >
        {clamped}
      </text>
    </svg>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">{title}</h3>
      {children}
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  multiline,
  rows,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  rows?: number
  placeholder?: string
}) {
  return (
    <div>
      <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">{label}</label>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows || 2}
          placeholder={placeholder}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      )}
    </div>
  )
}
