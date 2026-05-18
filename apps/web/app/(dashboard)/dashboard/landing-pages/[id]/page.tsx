'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Code2,
  Copy,
  Eye,
  FileText,
  Loader2,
  Plus,
  Save,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { landingPages, type LandingPageRow, type LandingSection } from '@/lib/api-client'
import { SectionRenderer } from '@/components/landing/SectionRenderer'

type SectionType =
  | 'hero'
  | 'features'
  | 'testimonials'
  | 'trust_badges'
  | 'faq'
  | 'gallery'
  | 'cta'
  | 'pricing'
  | 'lead_form'
  | 'rich_text'

const SECTION_TYPES: SectionType[] = [
  'hero',
  'features',
  'testimonials',
  'trust_badges',
  'faq',
  'gallery',
  'cta',
  'pricing',
  'lead_form',
  'rich_text',
]

const SECTION_LABELS: Record<string, string> = {
  hero: 'Hero',
  features: 'Features',
  testimonials: 'Testimonials',
  trust_badges: 'Trust Badges',
  faq: 'FAQ',
  gallery: 'Gallery',
  cta: 'Call To Action',
  pricing: 'Pricing',
  lead_form: 'Lead Form',
  rich_text: 'Rich Text',
}

const fieldClass =
  'mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/20'
const labelClass = 'text-xs font-semibold uppercase tracking-widest text-brand-forest-800'

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function asRecordArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.map(asRecord) : []
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => (typeof item === 'string' ? item : '')) : []
}

function createSection(type: SectionType): LandingSection {
  const base: Record<SectionType, Record<string, unknown>> = {
    hero: {
      eyebrow: 'Growth-focused landing page',
      headline: 'Turn more visitors into paying customers',
      subheadline: 'Use CustomerFlow to launch polished lead-capture pages quickly.',
      primary_cta_text: 'Get a free quote',
      secondary_cta_text: 'See how it works',
    },
    features: {
      title: 'Why customers choose us',
      items: [
        { title: 'Fast setup', description: 'Launch a focused page without waiting on a developer.' },
        { title: 'Built for leads', description: 'Every section is designed to guide visitors to enquire.' },
      ],
    },
    testimonials: {
      title: 'What customers say',
      items: [{ quote: 'The page helped us capture better enquiries in the first week.', author: 'Happy Customer', role: 'Owner' }],
    },
    trust_badges: {
      title: 'Trusted by local businesses',
      items: [{ label: 'Verified service' }, { label: 'Fast response' }, { label: 'Transparent pricing' }],
    },
    faq: {
      title: 'Frequently asked questions',
      items: [{ question: 'How quickly can we start?', answer: 'Most pages can be launched the same day.' }],
    },
    gallery: {
      title: 'Visual direction',
      image_briefs: ['Team helping a customer', 'Service result close-up', 'Friendly consultation'],
    },
    cta: {
      headline: 'Ready to grow?',
      subheadline: 'Send an enquiry and we will get back to you quickly.',
      primary_cta_text: 'Start now',
    },
    pricing: {
      title: 'Simple pricing',
      plans: [
        { name: 'Starter', price_text: 'From £49', features: ['Lead capture page', 'Mobile responsive'], cta_text: 'Enquire now', featured: true },
      ],
    },
    lead_form: {
      title: 'Get a free quote',
      subheadline: 'Tell us what you need and we will respond shortly.',
      submit_text: 'Send enquiry',
      fields: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'message', label: 'Message', type: 'textarea', required: false },
      ],
    },
    rich_text: {
      markdown: 'Add helpful supporting copy for your visitors here.',
    },
  }
  return { type, props: base[type] }
}

export default function LandingPageEditor({
  params,
}: {
  params: { id: string }
}) {
  const { id } = params
  const router = useRouter()
  const qc = useQueryClient()

  const { data: page, isLoading } = useQuery<LandingPageRow>({
    queryKey: ['landing-page', id],
    queryFn: () => landingPages.get(id).then((r) => r.data),
  })

  const [title, setTitle] = useState('')
  const [meta, setMeta] = useState('')
  const [sections, setSections] = useState<LandingSection[]>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [sectionsJson, setSectionsJson] = useState('[]')
  const [error, setError] = useState('')

  useEffect(() => {
    if (page) {
      setTitle(page.title)
      setMeta(page.meta_description || '')
      setSections(page.sections)
      setActiveIndex(0)
    }
  }, [page])

  useEffect(() => {
    if (!advancedOpen) setSectionsJson(JSON.stringify(sections, null, 2))
  }, [advancedOpen, sections])

  const save = useMutation({
    mutationFn: () => {
      if (!title.trim()) throw new Error('Page title is required')
      if (!sections.length) throw new Error('Add at least one landing page section')
      for (const section of sections) {
        if (!SECTION_TYPES.includes(section.type as SectionType)) {
          throw new Error(`Unsupported section type: ${section.type}`)
        }
      }
      return landingPages.update(id, {
        title,
        meta_description: meta || null,
        sections,
      })
    },
    onSuccess: () => {
      setError('')
      qc.invalidateQueries({ queryKey: ['landing-page', id] })
      qc.invalidateQueries({ queryKey: ['landing-pages'] })
    },
    onError: (e: Error) => setError(e.message),
  })

  const togglePublish = useMutation({
    mutationFn: () => landingPages.update(id, { is_published: !page?.is_published }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['landing-page', id] })
      qc.invalidateQueries({ queryKey: ['landing-pages'] })
    },
  })

  const remove = useMutation({
    mutationFn: () => landingPages.remove(id),
    onSuccess: () => router.push('/dashboard/landing-pages'),
  })

  if (isLoading || !page) {
    return <div className="py-20 text-center text-muted-foreground text-sm">Loading page...</div>
  }

  const primaryColor =
    asString((page.theme as { primary_color?: unknown; primary?: unknown })?.primary_color) ||
    asString((page.theme as { primary_color?: unknown; primary?: unknown })?.primary) ||
    '#166534'
  const activeSection = sections[activeIndex]
  let parseError = ''
  if (advancedOpen) {
    try {
      const parsed = JSON.parse(sectionsJson)
      if (!Array.isArray(parsed)) parseError = 'sections must be a JSON array'
    } catch (e) {
      parseError = (e as Error).message
    }
  }

  function updateSection(index: number, next: LandingSection) {
    setSections((curr) => curr.map((section, i) => (i === index ? next : section)))
  }

  function updateProps(index: number, key: string, value: unknown) {
    const section = sections[index]
    if (!section) return
    updateSection(index, { ...section, props: { ...asRecord(section.props), [key]: value } })
  }

  function moveSection(index: number, direction: -1 | 1) {
    const nextIndex = index + direction
    if (nextIndex < 0 || nextIndex >= sections.length) return
    setSections((curr) => {
      const next = [...curr]
      const [item] = next.splice(index, 1)
      next.splice(nextIndex, 0, item)
      return next
    })
    setActiveIndex(nextIndex)
  }

  function addSection(type: SectionType) {
    setSections((curr) => {
      const next = [...curr, createSection(type)]
      setActiveIndex(next.length - 1)
      return next
    })
  }

  function duplicateSection(index: number) {
    const section = sections[index]
    if (!section) return
    setSections((curr) => {
      const next = [...curr]
      next.splice(index + 1, 0, JSON.parse(JSON.stringify(section)))
      return next
    })
    setActiveIndex(index + 1)
  }

  function removeSection(index: number) {
    setSections((curr) => curr.filter((_, i) => i !== index))
    setActiveIndex((curr) => Math.max(0, Math.min(curr, sections.length - 2)))
  }

  function applyJson() {
    try {
      const parsed = JSON.parse(sectionsJson)
      if (!Array.isArray(parsed)) throw new Error('sections must be a JSON array')
      setSections(parsed as LandingSection[])
      setAdvancedOpen(false)
      setError('')
    } catch (e) {
      setError('Invalid JSON: ' + (e as Error).message)
    }
  }

  return (
    <div className="space-y-6">
      <header className="overflow-hidden rounded-2xl border border-brand-forest-100 bg-gradient-to-br from-brand-forest-50 via-white to-brand-teal-50 p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              href="/dashboard/landing-pages"
              className="inline-flex items-center gap-1 text-sm font-medium text-brand-forest-700 hover:text-brand-forest-950"
            >
              <ArrowLeft className="h-4 w-4" /> Back to landing pages
            </Link>
            <div className="mt-4 flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-forest-700 text-brand-forest-foreground shadow-brand">
                <Sparkles className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-brand-forest-700/80">
                  WYSIWYG Landing Page Editor
                </p>
                <h1 className="text-2xl font-bold tracking-tight text-brand-forest-950">{page.title}</h1>
                <p className="mt-1 text-sm text-brand-forest-800/70">
                  Edit copy, sections, and page structure visually while keeping the live preview in sync.
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <code className="rounded-lg border border-brand-forest-100 bg-white/80 px-2.5 py-1.5 text-xs text-brand-forest-800">
              /{page.slug}
            </code>
            <Link
              href={`/preview/landing/${page.slug}?id=${page.id}`}
              target="_blank"
              className="inline-flex items-center gap-1 rounded-lg border border-brand-forest-200 bg-white/80 px-3 py-2 text-sm font-semibold text-brand-forest-800 hover:bg-white"
            >
              <Eye className="h-4 w-4" /> Preview
            </Link>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2">
          <button
            onClick={() => togglePublish.mutate()}
            disabled={togglePublish.isPending}
            className={`rounded-lg px-3 py-2 text-sm font-semibold ${
              page.is_published
                ? 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                : 'bg-brand-forest-700 text-brand-forest-foreground shadow-brand hover:bg-brand-forest-800'
            }`}
          >
            {page.is_published ? 'Unpublish' : 'Publish'}
          </button>
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save page
          </button>
          <button
            onClick={() => {
              if (confirm(`Delete "${page.title}"?`)) remove.mutate()
            }}
            className="rounded-lg border border-red-200 bg-white/70 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <aside className="space-y-4 xl:sticky xl:top-4 xl:h-fit">
          <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <FileText className="h-4 w-4 text-brand-teal-600" />
              <h2 className="text-sm font-semibold uppercase tracking-widest text-brand-forest-800">Page settings</h2>
            </div>
            <label className={labelClass}>Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className={fieldClass}
            />
            <label className={`mt-4 block ${labelClass}`}>Meta description</label>
            <textarea
              value={meta}
              onChange={(e) => setMeta(e.target.value)}
              rows={3}
              className={fieldClass}
            />
            <p className="mt-1 text-xs text-muted-foreground">{meta.length} / 155 recommended characters</p>
          </section>

          <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-brand-forest-800">Sections</h2>
              <span className="rounded-full bg-brand-forest-50 px-2 py-0.5 text-xs font-semibold text-brand-forest-700">
                {sections.length}
              </span>
            </div>
            <div className="space-y-2">
              {sections.map((section, index) => (
                <button
                  key={`${section.type}-${index}`}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                  className={`flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left transition ${
                    activeIndex === index
                      ? 'border-brand-forest-400 bg-brand-forest-50 text-brand-forest-950 shadow-sm'
                      : 'border-border bg-background hover:border-brand-forest-200 hover:bg-brand-forest-50/40'
                  }`}
                >
                  <span>
                    <span className="block text-sm font-semibold">{SECTION_LABELS[section.type] || section.type}</span>
                    <span className="text-xs text-muted-foreground">Section {index + 1}</span>
                  </span>
                  <span className="text-xs font-mono text-muted-foreground">#{index + 1}</span>
                </button>
              ))}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {SECTION_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => addSection(type)}
                  className="inline-flex items-center justify-center gap-1 rounded-lg border border-border bg-background px-2 py-2 text-xs font-semibold text-brand-forest-800 hover:border-brand-forest-300 hover:bg-brand-forest-50"
                >
                  <Plus className="h-3.5 w-3.5" /> {SECTION_LABELS[type]}
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <button
              type="button"
              onClick={() => setAdvancedOpen((value) => !value)}
              className="flex w-full items-center justify-between text-sm font-semibold text-brand-forest-800"
            >
              <span className="inline-flex items-center gap-2">
                <Code2 className="h-4 w-4 text-brand-teal-600" /> Advanced JSON
              </span>
              <span>{advancedOpen ? 'Hide' : 'Show'}</span>
            </button>
            {advancedOpen && (
              <div className="mt-4 space-y-3">
                <p className="text-xs text-muted-foreground">
                  Use this only for precise schema edits. Applying JSON will replace the visual section state.
                </p>
                <textarea
                  value={sectionsJson}
                  onChange={(e) => setSectionsJson(e.target.value)}
                  rows={12}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono text-xs focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/20"
                  spellCheck={false}
                />
                {parseError && <p className="text-xs text-red-600">{parseError}</p>}
                <button
                  type="button"
                  onClick={applyJson}
                  disabled={Boolean(parseError)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-forest-700 px-3 py-2 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50"
                >
                  Apply JSON
                </button>
              </div>
            )}
          </section>
        </aside>

        <main className="space-y-6">
          <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            {activeSection ? (
              <>
                <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-brand-forest-700/80">
                      Editing section {activeIndex + 1}
                    </p>
                    <h2 className="text-xl font-bold text-brand-forest-950">
                      {SECTION_LABELS[activeSection.type] || activeSection.type}
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => moveSection(activeIndex, -1)}
                      disabled={activeIndex === 0}
                      className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-brand-forest-50 hover:text-brand-forest-800 disabled:opacity-40"
                      title="Move up"
                    >
                      <ArrowUp className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => moveSection(activeIndex, 1)}
                      disabled={activeIndex === sections.length - 1}
                      className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-brand-forest-50 hover:text-brand-forest-800 disabled:opacity-40"
                      title="Move down"
                    >
                      <ArrowDown className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => duplicateSection(activeIndex)}
                      className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-brand-forest-50 hover:text-brand-forest-800"
                      title="Duplicate"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => removeSection(activeIndex)}
                      className="rounded-lg border border-red-200 p-2 text-red-500 hover:bg-red-50"
                      title="Remove"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <SectionForm
                  section={activeSection}
                  onChange={(next) => updateSection(activeIndex, next)}
                  onPropChange={(key, value) => updateProps(activeIndex, key, value)}
                />
              </>
            ) : (
              <div className="rounded-xl border border-dashed border-brand-forest-200 bg-brand-forest-50/40 p-10 text-center">
                <Sparkles className="mx-auto h-8 w-8 text-brand-teal-600" />
                <h2 className="mt-3 text-lg font-semibold text-brand-forest-950">Add your first section</h2>
                <p className="mt-1 text-sm text-brand-forest-800/70">
                  Choose a section type from the left to start building this page visually.
                </p>
              </div>
            )}
            {error && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          </section>

          <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
            <header className="flex items-center justify-between border-b border-border bg-gradient-to-r from-brand-forest-50 to-brand-teal-50 px-5 py-3">
              <div>
                <h2 className="text-sm font-semibold text-brand-forest-950">Live preview</h2>
                <p className="text-xs text-brand-forest-800/70">Updates as you edit the section fields.</p>
              </div>
              <Eye className="h-4 w-4 text-brand-teal-600" />
            </header>
            <div className="max-h-[82vh] overflow-y-auto bg-white">
              {sections.map((s, i) => (
                <SectionRenderer key={i} section={s} primaryColor={primaryColor} />
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

function SectionForm({
  section,
  onChange,
  onPropChange,
}: {
  section: LandingSection
  onChange: (section: LandingSection) => void
  onPropChange: (key: string, value: unknown) => void
}) {
  const props = asRecord(section.props)

  function changeType(nextType: SectionType) {
    onChange(createSection(nextType))
  }

  return (
    <div className="space-y-5">
      <div>
        <label className={labelClass}>Section type</label>
        <select
          value={section.type}
          onChange={(e) => changeType(e.target.value as SectionType)}
          className={fieldClass}
        >
          {SECTION_TYPES.map((type) => (
            <option key={type} value={type}>
              {SECTION_LABELS[type]}
            </option>
          ))}
        </select>
      </div>

      {section.type === 'hero' && (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Eyebrow" value={asString(props.eyebrow)} onChange={(v) => onPropChange('eyebrow', v)} />
          <TextField label="Primary CTA" value={asString(props.primary_cta_text)} onChange={(v) => onPropChange('primary_cta_text', v)} />
          <TextField className="md:col-span-2" label="Headline" value={asString(props.headline)} onChange={(v) => onPropChange('headline', v)} />
          <TextAreaField className="md:col-span-2" label="Subheadline" value={asString(props.subheadline) || asString(props.sub)} onChange={(v) => onPropChange('subheadline', v)} />
          <TextField label="Secondary CTA" value={asString(props.secondary_cta_text)} onChange={(v) => onPropChange('secondary_cta_text', v)} />
        </div>
      )}

      {section.type === 'features' && (
        <ItemsEditor
          label="Feature cards"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          items={asRecordArray(props.items)}
          fields={[
            { key: 'title', label: 'Title' },
            { key: 'description', label: 'Description', multiline: true },
          ]}
          onChange={(items) => onPropChange('items', items)}
          emptyItem={{ title: 'New feature', description: 'Explain the benefit clearly.' }}
        />
      )}

      {section.type === 'testimonials' && (
        <ItemsEditor
          label="Testimonials"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          items={asRecordArray(props.items)}
          fields={[
            { key: 'quote', label: 'Quote', multiline: true },
            { key: 'author', label: 'Author' },
            { key: 'role', label: 'Role' },
          ]}
          onChange={(items) => onPropChange('items', items)}
          emptyItem={{ quote: 'Add a customer quote.', author: 'Customer name', role: 'Customer' }}
        />
      )}

      {section.type === 'trust_badges' && (
        <ItemsEditor
          label="Trust badges"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          items={asRecordArray(props.items)}
          fields={[{ key: 'label', label: 'Badge label' }]}
          onChange={(items) => onPropChange('items', items)}
          emptyItem={{ label: 'Trusted service' }}
        />
      )}

      {section.type === 'faq' && (
        <ItemsEditor
          label="FAQ questions"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          items={asRecordArray(props.items)}
          fields={[
            { key: 'question', label: 'Question' },
            { key: 'answer', label: 'Answer', multiline: true },
          ]}
          onChange={(items) => onPropChange('items', items)}
          emptyItem={{ question: 'New question?', answer: 'Answer the question here.' }}
        />
      )}

      {section.type === 'gallery' && (
        <StringListEditor
          label="Image briefs"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          values={asStringArray(props.image_briefs)}
          onChange={(values) => onPropChange('image_briefs', values)}
        />
      )}

      {section.type === 'cta' && (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField className="md:col-span-2" label="Headline" value={asString(props.headline)} onChange={(v) => onPropChange('headline', v)} />
          <TextAreaField className="md:col-span-2" label="Subheadline" value={asString(props.subheadline)} onChange={(v) => onPropChange('subheadline', v)} />
          <TextField label="CTA text" value={asString(props.primary_cta_text)} onChange={(v) => onPropChange('primary_cta_text', v)} />
        </div>
      )}

      {section.type === 'pricing' && (
        <ItemsEditor
          label="Pricing plans"
          titleValue={asString(props.title)}
          onTitleChange={(v) => onPropChange('title', v)}
          items={asRecordArray(props.plans)}
          fields={[
            { key: 'name', label: 'Plan name' },
            { key: 'price_text', label: 'Price' },
            { key: 'features', label: 'Features, comma-separated' },
            { key: 'cta_text', label: 'CTA text' },
          ]}
          onChange={(items) => onPropChange('plans', items.map((item) => ({ ...item, features: asString(item.features).split(',').map((v) => v.trim()).filter(Boolean) })))}
          emptyItem={{ name: 'New plan', price_text: 'From £99', features: 'Feature one, Feature two', cta_text: 'Choose plan' }}
        />
      )}

      {section.type === 'lead_form' && (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Form title" value={asString(props.title)} onChange={(v) => onPropChange('title', v)} />
          <TextField label="Submit button" value={asString(props.submit_text)} onChange={(v) => onPropChange('submit_text', v)} />
          <TextAreaField className="md:col-span-2" label="Subheadline" value={asString(props.subheadline)} onChange={(v) => onPropChange('subheadline', v)} />
        </div>
      )}

      {section.type === 'rich_text' && (
        <TextAreaField
          label="Content"
          value={asString(props.markdown)}
          onChange={(v) => onPropChange('markdown', v)}
          rows={8}
        />
      )}
    </div>
  )
}

function TextField({
  label,
  value,
  onChange,
  className = '',
}: {
  label: string
  value: string
  onChange: (value: string) => void
  className?: string
}) {
  return (
    <label className={className}>
      <span className={labelClass}>{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} className={fieldClass} />
    </label>
  )
}

function TextAreaField({
  label,
  value,
  onChange,
  className = '',
  rows = 4,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  className?: string
  rows?: number
}) {
  return (
    <label className={className}>
      <span className={labelClass}>{label}</span>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={rows} className={fieldClass} />
    </label>
  )
}

function ItemsEditor({
  label,
  titleValue,
  onTitleChange,
  items,
  fields,
  onChange,
  emptyItem,
}: {
  label: string
  titleValue: string
  onTitleChange: (value: string) => void
  items: Record<string, unknown>[]
  fields: { key: string; label: string; multiline?: boolean }[]
  onChange: (items: Record<string, unknown>[]) => void
  emptyItem: Record<string, unknown>
}) {
  const updateItem = (index: number, key: string, value: string) => {
    onChange(items.map((item, i) => (i === index ? { ...item, [key]: value } : item)))
  }

  return (
    <div className="space-y-4">
      <TextField label="Section title" value={titleValue} onChange={onTitleChange} />
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-brand-forest-950">{label}</h3>
        <button
          type="button"
          onClick={() => onChange([...items, emptyItem])}
          className="inline-flex items-center gap-1 rounded-lg bg-brand-forest-50 px-2.5 py-1.5 text-xs font-semibold text-brand-forest-800 hover:bg-brand-forest-100"
        >
          <Plus className="h-3.5 w-3.5" /> Add
        </button>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="rounded-xl border border-border bg-background p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Item {index + 1}
              </span>
              <button
                type="button"
                onClick={() => onChange(items.filter((_, i) => i !== index))}
                className="text-xs font-semibold text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {fields.map((field) => {
                const raw = item[field.key]
                const value = Array.isArray(raw) ? raw.join(', ') : asString(raw)
                return field.multiline ? (
                  <TextAreaField
                    key={field.key}
                    className="md:col-span-2"
                    label={field.label}
                    value={value}
                    onChange={(v) => updateItem(index, field.key, v)}
                    rows={3}
                  />
                ) : (
                  <TextField
                    key={field.key}
                    label={field.label}
                    value={value}
                    onChange={(v) => updateItem(index, field.key, v)}
                  />
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StringListEditor({
  label,
  titleValue,
  onTitleChange,
  values,
  onChange,
}: {
  label: string
  titleValue: string
  onTitleChange: (value: string) => void
  values: string[]
  onChange: (values: string[]) => void
}) {
  return (
    <div className="space-y-4">
      <TextField label="Section title" value={titleValue} onChange={onTitleChange} />
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-brand-forest-950">{label}</h3>
        <button
          type="button"
          onClick={() => onChange([...values, 'New image brief'])}
          className="inline-flex items-center gap-1 rounded-lg bg-brand-forest-50 px-2.5 py-1.5 text-xs font-semibold text-brand-forest-800 hover:bg-brand-forest-100"
        >
          <Plus className="h-3.5 w-3.5" /> Add
        </button>
      </div>
      <div className="space-y-3">
        {values.map((value, index) => (
          <div key={index} className="flex gap-2">
            <textarea
              value={value}
              onChange={(e) => onChange(values.map((item, i) => (i === index ? e.target.value : item)))}
              rows={2}
              className={fieldClass}
            />
            <button
              type="button"
              onClick={() => onChange(values.filter((_, i) => i !== index))}
              className="h-10 rounded-lg border border-red-200 px-2 text-red-500 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
