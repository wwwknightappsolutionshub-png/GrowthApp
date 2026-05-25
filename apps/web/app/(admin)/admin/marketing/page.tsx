'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  Eye,
  EyeOff,
  GripVertical,
  Loader2,
  Plus,
  Save,
  FileJson,
  AlertTriangle,
  LayoutTemplate,
} from 'lucide-react'
import { toast } from 'sonner'

import { MarketingSectionDataForm } from '@/components/admin/MarketingSectionDataForm'
import { admin } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface Section {
  id: string
  key: string
  title: string | null
  description: string | null
  data: Record<string, unknown>
  is_published: boolean
  sort_order: number
  updated_at: string
}

function SortableSectionRow({
  section,
  selectedKey,
  onSelect,
}: {
  section: Section
  selectedKey: string | null
  onSelect: (key: string) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: section.key,
  })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }
  return (
    <li ref={setNodeRef} style={style} className={cn(isDragging && 'z-50 opacity-90')}>
      <div
        className={cn(
          'flex w-full items-stretch gap-0.5 rounded-md border border-transparent',
          selectedKey === section.key ? 'border-amber-500/40 bg-amber-500/10' : 'hover:border-gray-700',
        )}
      >
        <button
          type="button"
          className="flex shrink-0 cursor-grab touch-none items-center px-1 text-gray-500 hover:text-gray-300 active:cursor-grabbing"
          {...attributes}
          {...listeners}
          aria-label="Drag to reorder"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => onSelect(section.key)}
          className={cn(
            'flex min-w-0 flex-1 flex-col rounded-md py-2 pr-2 text-left text-sm transition-colors',
            selectedKey === section.key ? 'text-amber-100' : 'text-gray-300 hover:text-white',
          )}
        >
          <span className="truncate font-medium leading-tight">{section.title || section.key}</span>
          <span className="font-mono text-[10px] text-gray-500">{section.key}</span>
        </button>
        <span className="flex shrink-0 items-center pr-2">
          {section.is_published ? (
            <Eye className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <EyeOff className="h-3.5 w-3.5 text-gray-500" />
          )}
        </span>
      </div>
    </li>
  )
}

export default function AdminMarketingPage() {
  const [sections, setSections] = useState<Section[]>([])
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [addOpen, setAddOpen] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  useEffect(() => {
    void refresh()
  }, [])

  async function refresh() {
    setLoading(true)
    setLoadError(null)
    try {
      const res = await admin.listMarketingSections()
      const rows = res.data as Section[]
      rows.sort((a, b) => a.sort_order - b.sort_order || a.key.localeCompare(b.key))
      setSections(rows)
      setSelectedKey((prev) => {
        if (prev && rows.some((s) => s.key === prev)) return prev
        return rows[0]?.key ?? null
      })
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string }
      const detail = e.response?.data?.detail || e.message || 'Unknown error'
      setLoadError(String(detail))
      toast.error('Failed to load marketing sections')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function seedDefaults() {
    setSeeding(true)
    try {
      await admin.seedMarketingDefaults()
      toast.success('Default marketing sections loaded')
      await refresh()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not seed defaults')
      console.error(err)
    } finally {
      setSeeding(false)
    }
  }

  async function onDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = sections.findIndex((s) => s.key === active.id)
    const newIndex = sections.findIndex((s) => s.key === over.id)
    if (oldIndex < 0 || newIndex < 0) return
    const next = arrayMove(sections, oldIndex, newIndex)
    setSections(next)
    try {
      await admin.reorderMarketingSections({ keys: next.map((s) => s.key) })
      toast.success('Section order saved')
      await refresh()
    } catch (err) {
      toast.error('Could not save order')
      console.error(err)
      await refresh()
    }
  }

  const selected = useMemo(
    () => sections.find((s) => s.key === selectedKey) ?? null,
    [sections, selectedKey],
  )

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Marketing CMS</h1>
          <p className="mt-1 text-sm text-gray-400">
            Edit the public site with visual forms, reorder sections for your sidebar, or jump into raw JSON.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="inline-flex items-center gap-2 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          <Plus className="h-4 w-4" />
          New section
        </button>
      </header>

      <div className="grid gap-5 lg:grid-cols-[300px,1fr]">
        <aside className="rounded-lg border border-gray-800 bg-gray-900/60 p-3">
          <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-500">
            Sections · drag to reorder
          </p>
          {loading && <p className="px-2 py-3 text-xs text-gray-500">Loading…</p>}
          {!loading && loadError && (
            <div className="space-y-2 px-2 py-3">
              <p className="text-xs text-rose-300">{loadError}</p>
              <p className="text-[11px] text-gray-500">
                If this is a fresh deploy, run database migrations on the API server, then retry.
              </p>
              <button
                type="button"
                onClick={() => void refresh()}
                className="rounded-md border border-gray-700 px-2 py-1 text-xs text-gray-200 hover:bg-gray-800"
              >
                Retry
              </button>
            </div>
          )}
          {!loading && !loadError && sections.length === 0 && (
            <div className="space-y-2 px-2 py-3">
              <p className="text-xs text-gray-400">No sections yet.</p>
              <button
                type="button"
                disabled={seeding}
                onClick={() => void seedDefaults()}
                className="inline-flex items-center gap-2 rounded-md bg-amber-500 px-2.5 py-1.5 text-xs font-semibold text-gray-950 hover:bg-amber-400 disabled:opacity-50"
              >
                {seeding ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                Load defaults
              </button>
            </div>
          )}
          {!loading && !loadError && sections.length > 0 && (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
              <SortableContext items={sections.map((s) => s.key)} strategy={verticalListSortingStrategy}>
                <ul className="space-y-1">
                  {sections.map((s) => (
                    <SortableSectionRow
                      key={s.key}
                      section={s}
                      selectedKey={selectedKey}
                      onSelect={setSelectedKey}
                    />
                  ))}
                </ul>
              </SortableContext>
            </DndContext>
          )}
        </aside>

        <section className="rounded-lg border border-gray-800 bg-gray-900/40 p-5">
          {!selected ? (
            <p className="text-sm text-gray-400">Select or create a section.</p>
          ) : (
            <SectionEditor section={selected} onSaved={refresh} />
          )}
        </section>
      </div>

      {addOpen && (
        <AddSectionDialog
          existingKeys={new Set(sections.map((s) => s.key))}
          nextSortOrder={sections.length ? Math.max(...sections.map((s) => s.sort_order)) + 10 : 10}
          onClose={() => setAddOpen(false)}
          onCreated={async (key) => {
            setAddOpen(false)
            await refresh()
            setSelectedKey(key)
          }}
        />
      )}
    </div>
  )
}

function AddSectionDialog({
  existingKeys,
  nextSortOrder,
  onClose,
  onCreated,
}: {
  existingKeys: Set<string>
  nextSortOrder: number
  onClose: () => void
  onCreated: (key: string) => void
}) {
  const [key, setKey] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    const slug = key.trim().toLowerCase().replace(/\s+/g, '-')
    if (!/^[a-z0-9][a-z0-9-]{0,62}$/.test(slug)) {
      toast.error('Use a short slug: letters, numbers and hyphens (e.g. trust-bar).')
      return
    }
    if (existingKeys.has(slug)) {
      toast.error('That key already exists.')
      return
    }
    setBusy(true)
    try {
      await admin.upsertMarketingSection({
        key: slug,
        title: title.trim() || slug,
        description: description.trim() || null,
        data: { items: [] },
        is_published: false,
        sort_order: nextSortOrder,
      })
      toast.success('Section created (draft)')
      await onCreated(slug)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not create section')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-900 p-5 shadow-xl">
        <div className="mb-4 flex items-center gap-2 text-white">
          <LayoutTemplate className="h-5 w-5 text-amber-400" />
          <h2 className="text-lg font-semibold">New marketing section</h2>
        </div>
        <p className="mb-4 text-xs text-gray-400">
          Creates a draft section. The public homepage only renders known blocks (hero, stats, …); custom keys are
          available for future pages or API consumers.
        </p>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">Key (slug)</label>
            <input
              className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
              placeholder="e.g. trust-bar"
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">Title</label>
            <input
              className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
              placeholder="Display name in CMS"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">Description (optional)</label>
            <input
              className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-md px-3 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void submit()}
            className="inline-flex items-center gap-2 rounded-md bg-amber-500 px-3 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Create draft
          </button>
        </div>
      </div>
    </div>
  )
}

function SectionEditor({ section, onSaved }: { section: Section; onSaved: () => void }) {
  const [tab, setTab] = useState<'visual' | 'json'>('visual')
  const [draft, setDraft] = useState(() => JSON.stringify(section.data, null, 2))
  const [visualData, setVisualData] = useState<Record<string, unknown>>(() => ({ ...section.data }))
  const [isPublished, setIsPublished] = useState(section.is_published)
  const [saving, setSaving] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)

  useEffect(() => {
    setDraft(JSON.stringify(section.data, null, 2))
    setVisualData({ ...section.data })
    setIsPublished(section.is_published)
    setParseError(null)
  }, [section.key, section.updated_at, section.data, section.is_published])

  useEffect(() => {
    if (tab === 'visual') setDraft(JSON.stringify(visualData, null, 2))
  }, [visualData, tab])

  async function save() {
    setParseError(null)
    let parsed: Record<string, unknown>
    if (tab === 'json') {
      try {
        parsed = JSON.parse(draft)
      } catch (err) {
        setParseError((err as Error).message)
        return
      }
    } else {
      parsed = visualData
    }
    setSaving(true)
    try {
      await admin.patchMarketingSection(section.key, {
        data: parsed,
        is_published: isPublished,
      })
      toast.success('Section saved')
      onSaved()
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">{section.title || section.key}</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            {section.description || 'Content for the public marketing site.'}
          </p>
          <p className="mt-1 font-mono text-[10px] text-gray-600">
            key: {section.key} · sort: {section.sort_order} · updated {new Date(section.updated_at).toLocaleString('en-GB')}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-md border border-gray-700 p-0.5">
            <button
              type="button"
              onClick={() => {
                try {
                  setVisualData(JSON.parse(draft))
                  setTab('visual')
                } catch {
                  toast.error('JSON is invalid — fix errors before using the visual editor.')
                }
              }}
              className={cn(
                'rounded px-2.5 py-1.5 text-xs font-medium',
                tab === 'visual' ? 'bg-amber-500/20 text-amber-200' : 'text-gray-400 hover:text-white',
              )}
            >
              Visual
            </button>
            <button
              type="button"
              onClick={() => {
                setTab('json')
                setDraft(JSON.stringify(visualData, null, 2))
              }}
              className={cn(
                'rounded px-2.5 py-1.5 text-xs font-medium',
                tab === 'json' ? 'bg-amber-500/20 text-amber-200' : 'text-gray-400 hover:text-white',
              )}
            >
              JSON
            </button>
          </div>
          <label className="inline-flex items-center gap-2 text-xs text-gray-400">
            <input
              type="checkbox"
              checked={isPublished}
              onChange={(e) => setIsPublished(e.target.checked)}
              className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-amber-500 focus:ring-amber-500"
            />
            Published
          </label>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-md bg-amber-500 px-3.5 py-2 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save
          </button>
        </div>
      </header>

      {tab === 'visual' ? (
        <MarketingSectionDataForm sectionKey={section.key} data={visualData} onChange={setVisualData} />
      ) : (
        <>
          <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-gray-500">
            <FileJson className="h-3 w-3" />
            Raw JSON
          </div>
          <textarea
            value={draft}
            spellCheck={false}
            onChange={(e) => setDraft(e.target.value)}
            className="h-[480px] w-full resize-y rounded-md border border-gray-800 bg-gray-950/80 p-4 font-mono text-xs text-gray-100 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/30"
          />
        </>
      )}

      {parseError && (
        <p className="mt-3 inline-flex items-center gap-2 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          <AlertTriangle className="h-3.5 w-3.5" />
          {parseError}
        </p>
      )}
    </div>
  )
}
