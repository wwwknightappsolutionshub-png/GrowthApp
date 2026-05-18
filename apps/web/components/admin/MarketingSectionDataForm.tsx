'use client'

import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'

import { cn } from '@/lib/utils'

type JsonRecord = Record<string, unknown>

function asStr(v: unknown, fallback = ''): string {
  return typeof v === 'string' ? v : v == null ? fallback : String(v)
}

function asNum(v: unknown, fallback = 0): number {
  if (typeof v === 'number' && !Number.isNaN(v)) return v
  if (typeof v === 'string') {
    const n = Number(v)
    return Number.isNaN(n) ? fallback : n
  }
  return fallback
}

function asBool(v: unknown): boolean {
  return v === true || v === 'true'
}

function asArr(v: unknown): unknown[] {
  return Array.isArray(v) ? v : []
}

const input =
  'w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-600 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/30'
const label = 'mb-1 block text-xs font-medium text-gray-400'
const btnGhost =
  'inline-flex items-center gap-1 rounded-md border border-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800'

export function MarketingSectionDataForm({
  sectionKey,
  data,
  onChange,
}: {
  sectionKey: string
  data: JsonRecord
  onChange: (next: JsonRecord) => void
}) {
  const patch = (partial: JsonRecord) => onChange({ ...data, ...partial })

  switch (sectionKey) {
    case 'hero':
      return <HeroForm data={data} patch={patch} />
    case 'stats':
      return <StatsForm data={data} patch={patch} />
    case 'industries':
      return <IndustriesForm data={data} patch={patch} />
    case 'pricing':
      return <PricingForm data={data} patch={patch} />
    case 'faqs':
      return <FaqsForm data={data} patch={patch} />
    case 'pillars':
      return <PillarsForm data={data} patch={patch} />
    case 'footer':
      return <FooterForm data={data} patch={patch} />
    default:
      return (
        <p className="rounded-md border border-dashed border-gray-700 bg-gray-950/50 p-4 text-sm text-gray-400">
          No visual form for <code className="font-mono text-amber-200/90">{sectionKey}</code> yet.
          Use the <strong className="text-gray-200">JSON</strong> tab to edit this section.
        </p>
      )
  }
}

function HeroForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const chips = asArr(data.trust_chips).map((c) =>
    typeof c === 'object' && c && 'label' in c ? asStr((c as { label?: unknown }).label) : '',
  )
  const setChip = (i: number, label: string) => {
    const next = [...chips]
    next[i] = label
    patch({ trust_chips: next.filter(Boolean).map((label) => ({ label })) })
  }
  const addChip = () => patch({ trust_chips: [...chips.map((l) => ({ label: l })), { label: 'New' }] })
  const removeChip = (i: number) => {
    const next = chips.filter((_, j) => j !== i)
    patch({ trust_chips: next.map((label) => ({ label })) })
  }
  const pc = data.primary_cta as { label?: unknown; href?: unknown } | undefined
  const sc = data.secondary_cta as { label?: unknown; href?: unknown } | undefined
  return (
    <div className="space-y-5">
      <Field label="Eyebrow">
        <input className={input} value={asStr(data.eyebrow)} onChange={(e) => patch({ eyebrow: e.target.value })} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Headline (line 1)">
          <input
            className={input}
            value={asStr(data.headline_part_1)}
            onChange={(e) => patch({ headline_part_1: e.target.value })}
          />
        </Field>
        <Field label="Headline (line 2)">
          <input
            className={input}
            value={asStr(data.headline_part_2)}
            onChange={(e) => patch({ headline_part_2: e.target.value })}
          />
        </Field>
      </div>
      <Field label="Subcopy">
        <textarea
          className={cn(input, 'min-h-[100px] resize-y')}
          value={asStr(data.sub)}
          onChange={(e) => patch({ sub: e.target.value })}
        />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Primary CTA label">
          <input
            className={input}
            value={asStr(pc?.label)}
            onChange={(e) => patch({ primary_cta: { ...(pc || {}), label: e.target.value, href: asStr(pc?.href, '/') } })}
          />
        </Field>
        <Field label="Primary CTA link">
          <input
            className={input}
            value={asStr(pc?.href)}
            onChange={(e) => patch({ primary_cta: { ...(pc || {}), label: asStr(pc?.label, 'Go'), href: e.target.value } })}
          />
        </Field>
        <Field label="Secondary CTA label">
          <input
            className={input}
            value={asStr(sc?.label)}
            onChange={(e) => patch({ secondary_cta: { ...(sc || {}), label: e.target.value, href: asStr(sc?.href, '/') } })}
          />
        </Field>
        <Field label="Secondary CTA link">
          <input
            className={input}
            value={asStr(sc?.href)}
            onChange={(e) => patch({ secondary_cta: { ...(sc || {}), label: asStr(sc?.label, 'Learn more'), href: e.target.value } })}
          />
        </Field>
      </div>
      <Field label="Live status line">
        <input className={input} value={asStr(data.live_label)} onChange={(e) => patch({ live_label: e.target.value })} />
      </Field>
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className={label}>Trust chips</span>
          <button type="button" className={btnGhost} onClick={addChip}>
            <Plus className="h-3.5 w-3.5" /> Add chip
          </button>
        </div>
        <ul className="space-y-2">
          {chips.map((chip, i) => (
            <li key={i} className="flex gap-2">
              <input className={input} value={chip} onChange={(e) => setChip(i, e.target.value)} />
              <button type="button" className={btnGhost} onClick={() => removeChip(i)} aria-label="Remove">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function StatsForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const items = asArr(data.items).map((row) => {
    if (typeof row !== 'object' || !row) return { label: '', value: 0, suffix: '', tone: 'forest', help: '' }
    const o = row as JsonRecord
    return {
      label: asStr(o.label),
      value: asNum(o.value),
      suffix: asStr(o.suffix),
      tone: asStr(o.tone, 'forest'),
      help: asStr(o.help),
    }
  })
  const setItems = (next: typeof items) =>
    patch({
      items: next.map((it) => ({
        label: it.label,
        value: it.value,
        suffix: it.suffix,
        tone: it.tone,
        ...(it.help ? { help: it.help } : {}),
      })),
    })
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          type="button"
          className={btnGhost}
          onClick={() => setItems([...items, { label: 'Metric', value: 0, suffix: '', tone: 'teal', help: '' }])}
        >
          <Plus className="h-3.5 w-3.5" /> Add metric
        </button>
      </div>
      {items.map((it, i) => (
        <div key={i} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4 space-y-3">
          <div className="flex justify-end">
            <button type="button" className={btnGhost} onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <Trash2 className="h-3.5 w-3.5" /> Remove
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Label">
              <input className={input} value={it.label} onChange={(e) => {
                const n = [...items]; n[i] = { ...n[i], label: e.target.value }; setItems(n)
              }} />
            </Field>
            <Field label="Value (number)">
              <input
                type="number"
                className={input}
                value={it.value}
                onChange={(e) => {
                  const n = [...items]; n[i] = { ...n[i], value: Number(e.target.value) }; setItems(n)
                }}
              />
            </Field>
            <Field label="Suffix (e.g. +, s)">
              <input className={input} value={it.suffix} onChange={(e) => {
                const n = [...items]; n[i] = { ...n[i], suffix: e.target.value }; setItems(n)
              }} />
            </Field>
            <Field label="Tone">
              <select
                className={input}
                value={it.tone}
                onChange={(e) => {
                  const n = [...items]; n[i] = { ...n[i], tone: e.target.value }; setItems(n)
                }}
              >
                <option value="forest">forest</option>
                <option value="teal">teal</option>
              </select>
            </Field>
          </div>
          <Field label="Help text (optional)">
            <input className={input} value={it.help} onChange={(e) => {
              const n = [...items]; n[i] = { ...n[i], help: e.target.value }; setItems(n)
            }} />
          </Field>
        </div>
      ))}
    </div>
  )
}

function IndustriesForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const items = asArr(data.items).map((row) => {
    if (typeof row !== 'object' || !row) return { label: '', icon: 'Sparkles' }
    const o = row as JsonRecord
    return { label: asStr(o.label), icon: asStr(o.icon, 'Sparkles') }
  })
  const setItems = (next: typeof items) => patch({ items: next })
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button type="button" className={btnGhost} onClick={() => setItems([...items, { label: 'Industry', icon: 'Briefcase' }])}>
          <Plus className="h-3.5 w-3.5" /> Add row
        </button>
      </div>
      {items.map((it, i) => (
        <div key={i} className="flex gap-2">
          <input
            className={input}
            placeholder="Label"
            value={it.label}
            onChange={(e) => {
              const n = [...items]; n[i] = { ...n[i], label: e.target.value }; setItems(n)
            }}
          />
          <input
            className={cn(input, 'max-w-[180px]')}
            placeholder="Lucide icon name"
            value={it.icon}
            onChange={(e) => {
              const n = [...items]; n[i] = { ...n[i], icon: e.target.value }; setItems(n)
            }}
          />
          <button type="button" className={btnGhost} onClick={() => setItems(items.filter((_, j) => j !== i))}>
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}

function PricingForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const plans = asArr(data.plans).map((row) => {
    if (typeof row !== 'object' || !row) return {} as JsonRecord
    return row as JsonRecord
  })
  const setPlans = (next: JsonRecord[]) => patch({ plans: next })
  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Currency code">
          <input className={input} value={asStr(data.currency, 'GBP')} onChange={(e) => patch({ currency: e.target.value })} />
        </Field>
        <Field label="Symbol">
          <input className={input} value={asStr(data.currency_symbol, '£')} onChange={(e) => patch({ currency_symbol: e.target.value })} />
        </Field>
        <Field label="Period">
          <input className={input} value={asStr(data.period, 'month')} onChange={(e) => patch({ period: e.target.value })} />
        </Field>
      </div>
      <Field label="Footnote">
        <textarea className={cn(input, 'min-h-[72px]')} value={asStr(data.footnote)} onChange={(e) => patch({ footnote: e.target.value })} />
      </Field>
      <div className="flex justify-end">
        <button
          type="button"
          className={btnGhost}
          onClick={() =>
            setPlans([
              ...plans,
              {
                key: `plan_${plans.length + 1}`,
                name: 'New plan',
                price: 99,
                tagline: '',
                cta: 'Start trial',
                highlighted: false,
                features: ['Feature one', 'Feature two'],
              },
            ])
          }
        >
          <Plus className="h-3.5 w-3.5" /> Add plan
        </button>
      </div>
      {plans.map((p, i) => (
        <div key={i} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4 space-y-3">
          <div className="flex justify-end">
            <button type="button" className={btnGhost} onClick={() => setPlans(plans.filter((_, j) => j !== i))}>
              <Trash2 className="h-3.5 w-3.5" /> Remove plan
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Key (slug)">
              <input
                className={input}
                value={asStr(p.key)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], key: e.target.value }; setPlans(n)
                }}
              />
            </Field>
            <Field label="Name">
              <input
                className={input}
                value={asStr(p.name)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], name: e.target.value }; setPlans(n)
                }}
              />
            </Field>
            <Field label="Price (£ / mo)">
              <input
                type="number"
                className={input}
                value={asNum(p.price)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], price: Number(e.target.value) }; setPlans(n)
                }}
              />
            </Field>
            <Field label="Badge (optional)">
              <input
                className={input}
                value={asStr(p.badge)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], badge: e.target.value || undefined }; setPlans(n)
                }}
              />
            </Field>
            <Field label="Tagline">
              <input
                className={input}
                value={asStr(p.tagline)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], tagline: e.target.value }; setPlans(n)
                }}
              />
            </Field>
            <Field label="CTA label">
              <input
                className={input}
                value={asStr(p.cta)}
                onChange={(e) => {
                  const n = [...plans]; n[i] = { ...n[i], cta: e.target.value }; setPlans(n)
                }}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-xs text-gray-300">
            <input
              type="checkbox"
              checked={asBool(p.highlighted)}
              onChange={(e) => {
                const n = [...plans]; n[i] = { ...n[i], highlighted: e.target.checked }; setPlans(n)
              }}
              className="h-4 w-4 rounded border-gray-600"
            />
            Highlighted plan
          </label>
          <Field label="Features (one per line)">
            <textarea
              className={cn(input, 'min-h-[120px] font-mono text-xs')}
              value={asArr(p.features).map((f) => asStr(f)).join('\n')}
              onChange={(e) => {
                const feats = e.target.value.split('\n').map((s) => s.trim()).filter(Boolean)
                const n = [...plans]; n[i] = { ...n[i], features: feats }; setPlans(n)
              }}
            />
          </Field>
        </div>
      ))}
    </div>
  )
}

function FaqsForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const items = asArr(data.items).map((row) => {
    if (typeof row !== 'object' || !row) return { q: '', a: '' }
    const o = row as JsonRecord
    return { q: asStr(o.q), a: asStr(o.a) }
  })
  const setItems = (next: typeof items) => patch({ items: next })
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button type="button" className={btnGhost} onClick={() => setItems([...items, { q: 'Question?', a: 'Answer.' }])}>
          <Plus className="h-3.5 w-3.5" /> Add FAQ
        </button>
      </div>
      {items.map((it, i) => (
        <div key={i} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4 space-y-3">
          <div className="flex justify-end">
            <button type="button" className={btnGhost} onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
          <Field label="Question">
            <input className={input} value={it.q} onChange={(e) => {
              const n = [...items]; n[i] = { ...n[i], q: e.target.value }; setItems(n)
            }} />
          </Field>
          <Field label="Answer">
            <textarea className={cn(input, 'min-h-[88px]')} value={it.a} onChange={(e) => {
              const n = [...items]; n[i] = { ...n[i], a: e.target.value }; setItems(n)
            }} />
          </Field>
        </div>
      ))}
    </div>
  )
}

function PillarsForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const items = asArr(data.items).map((row) => {
    if (typeof row !== 'object' || !row) return { title: '', subtitle: '', icon: 'Target', tone: 'forest', bullets: [] as string[] }
    const o = row as JsonRecord
    return {
      title: asStr(o.title),
      subtitle: asStr(o.subtitle),
      icon: asStr(o.icon, 'Target'),
      tone: asStr(o.tone, 'forest'),
      bullets: asArr(o.bullets).map((b) => asStr(b)),
    }
  })
  const setItems = (next: typeof items) =>
    patch({
      items: next.map((it) => ({
        title: it.title,
        subtitle: it.subtitle,
        icon: it.icon,
        tone: it.tone,
        bullets: it.bullets,
      })),
    })
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          type="button"
          className={btnGhost}
          onClick={() =>
            setItems([
              ...items,
              { title: 'Pillar', subtitle: 'Subtitle', icon: 'Zap', tone: 'teal', bullets: ['Point one', 'Point two'] },
            ])
          }
        >
          <Plus className="h-3.5 w-3.5" /> Add pillar
        </button>
      </div>
      {items.map((it, i) => (
        <div key={i} className="rounded-lg border border-gray-800 bg-gray-950/40 p-4 space-y-3">
          <div className="flex justify-end">
            <button type="button" className={btnGhost} onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Title">
              <input className={input} value={it.title} onChange={(e) => {
                const n = [...items]; n[i] = { ...n[i], title: e.target.value }; setItems(n)
              }} />
            </Field>
            <Field label="Subtitle">
              <input className={input} value={it.subtitle} onChange={(e) => {
                const n = [...items]; n[i] = { ...n[i], subtitle: e.target.value }; setItems(n)
              }} />
            </Field>
            <Field label="Icon (Lucide name)">
              <input className={input} value={it.icon} onChange={(e) => {
                const n = [...items]; n[i] = { ...n[i], icon: e.target.value }; setItems(n)
              }} />
            </Field>
            <Field label="Tone">
              <select
                className={input}
                value={it.tone}
                onChange={(e) => {
                  const n = [...items]; n[i] = { ...n[i], tone: e.target.value }; setItems(n)
                }}
              >
                <option value="forest">forest</option>
                <option value="teal">teal</option>
              </select>
            </Field>
          </div>
          <Field label="Bullets (one per line)">
            <textarea
              className={cn(input, 'min-h-[100px] font-mono text-xs')}
              value={it.bullets.join('\n')}
              onChange={(e) => {
                const bullets = e.target.value.split('\n').map((s) => s.trim()).filter(Boolean)
                const n = [...items]; n[i] = { ...n[i], bullets }; setItems(n)
              }}
            />
          </Field>
        </div>
      ))}
    </div>
  )
}

function FooterForm({ data, patch }: { data: JsonRecord; patch: (p: JsonRecord) => void }) {
  const [linksJson, setLinksJson] = React.useState(() => JSON.stringify(data.links ?? {}, null, 2))
  React.useEffect(() => {
    setLinksJson(JSON.stringify(data.links ?? {}, null, 2))
  }, [data.links])
  return (
    <div className="space-y-5">
      <Field label="Tagline">
        <input className={input} value={asStr(data.tagline)} onChange={(e) => patch({ tagline: e.target.value })} />
      </Field>
      <Field label="Address line">
        <input className={input} value={asStr(data.address)} onChange={(e) => patch({ address: e.target.value })} />
      </Field>
      <Field label="Footer links (JSON — column groups)">
        <p className="mb-2 text-[11px] text-gray-500">
          Keep the structure <code className="font-mono text-gray-400">{'{ "Product": [{ "label", "href" }] }'}</code>.
        </p>
        <textarea
          spellCheck={false}
          className={cn(input, 'min-h-[220px] font-mono text-xs')}
          value={linksJson}
          onChange={(e) => setLinksJson(e.target.value)}
          onBlur={() => {
            try {
              patch({ links: JSON.parse(linksJson) as JsonRecord })
            } catch {
              setLinksJson(JSON.stringify(data.links ?? {}, null, 2))
            }
          }}
        />
      </Field>
    </div>
  )
}

function Field({ label: lab, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className={label}>{lab}</label>
      {children}
    </div>
  )
}
