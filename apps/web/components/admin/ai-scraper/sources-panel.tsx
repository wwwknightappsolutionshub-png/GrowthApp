'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import {
  aiScraper,
  type AiScraperCategory,
  type AiScraperSource,
  type ScraperType,
  type SourcePlatform,
} from '@/lib/api-client'
import {
  buttonDangerClass,
  buttonGhostClass,
  buttonPrimaryClass,
  EmptyRow,
  formatDate,
  inputClass,
  labelClass,
  SectionCard,
} from './shared'

const SCRAPING_TYPES: { value: ScraperType; label: string }[] = [
  { value: 'html', label: 'HTML page' },
  { value: 'api', label: 'API endpoint' },
  { value: 'directory', label: 'Business directory' },
  { value: 'social', label: 'Social network' },
  { value: 'custom', label: 'Custom adapter' },
]

const PLATFORM_TYPES: { value: SourcePlatform; label: string }[] = [
  { value: 'directory', label: 'Directory' },
  { value: 'search_engine', label: 'Search engine' },
  { value: 'social', label: 'Social' },
  { value: 'review_site', label: 'Review site' },
  { value: 'marketplace', label: 'Lead marketplace' },
  { value: 'other', label: 'Other' },
]

interface FormState {
  id: string | null
  name: string
  url_pattern: string
  scraping_type: ScraperType
  source_platform: SourcePlatform
  category_id: string
  active: boolean
  postcode_prefix: string
  region_label: string
  notes: string
}

const EMPTY: FormState = {
  id: null,
  name: '',
  url_pattern: '',
  scraping_type: 'html',
  source_platform: 'directory',
  category_id: '',
  active: true,
  postcode_prefix: '',
  region_label: '',
  notes: '',
}

export function SourcesPanel() {
  const qc = useQueryClient()
  const [form, setForm] = useState<FormState>(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterActive, setFilterActive] = useState<string>('')

  const { data: categories } = useQuery({
    queryKey: ['ai-scraper', 'categories'],
    queryFn: () => aiScraper.listCategories().then((r) => r.data),
  })

  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['ai-scraper', 'sources', filterCategory, filterActive],
    queryFn: () =>
      aiScraper
        .listSources({
          category_id: filterCategory || undefined,
          active:
            filterActive === '' ? undefined : filterActive === 'true',
        })
        .then((r) => r.data),
  })

  const categoryById = useMemo(() => {
    const map = new Map<string, AiScraperCategory>()
    categories?.forEach((c) => map.set(c.id, c))
    return map
  }, [categories])

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ['ai-scraper', 'sources'] })

  const create = useMutation({
    mutationFn: () =>
      aiScraper.createSource({
        name: form.name.trim(),
        url_pattern: form.url_pattern.trim(),
        scraping_type: form.scraping_type,
        source_platform: form.source_platform,
        category_id: form.category_id,
        active: form.active,
        postcode_prefix: form.postcode_prefix.trim() || null,
        region_label: form.region_label.trim() || null,
        notes: form.notes.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Source created')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to create source'),
  })

  const update = useMutation({
    mutationFn: () =>
      aiScraper.updateSource(form.id!, {
        name: form.name.trim(),
        url_pattern: form.url_pattern.trim(),
        scraping_type: form.scraping_type,
        source_platform: form.source_platform,
        category_id: form.category_id,
        active: form.active,
        postcode_prefix: form.postcode_prefix.trim() || null,
        region_label: form.region_label.trim() || null,
        notes: form.notes.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Source updated')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to update source'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => aiScraper.deleteSource(id),
    onSuccess: () => {
      toast.success('Source deleted')
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to delete source'),
  })

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.name.trim()) {
      toast.error('Name is required')
      return
    }
    if (!form.url_pattern.trim()) {
      toast.error('URL pattern is required')
      return
    }
    if (!form.category_id) {
      toast.error('Category is required')
      return
    }
    if (form.id) update.mutate()
    else create.mutate()
  }

  const onEdit = (src: AiScraperSource) => {
    setForm({
      id: src.id,
      name: src.name,
      url_pattern: src.url_pattern,
      scraping_type: src.scraping_type,
      source_platform: src.source_platform ?? 'directory',
      category_id: src.category_id,
      active: src.active,
      postcode_prefix: src.postcode_prefix ?? '',
      region_label: src.region_label ?? '',
      notes: src.notes ?? '',
    })
    setShowForm(true)
  }

  const onDelete = (src: AiScraperSource) => {
    if (!confirm(`Delete source "${src.name}"?`)) return
    remove.mutate(src.id)
  }

  const noCategories = !categories || categories.length === 0

  return (
    <SectionCard
      title="Sources"
      description="Where the scraper looks for raw leads — websites, APIs, or directories."
      actions={
        <button
          type="button"
          className={buttonPrimaryClass}
          disabled={noCategories}
          onClick={() => {
            setForm(EMPTY)
            setShowForm((v) => !v)
          }}
        >
          {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {showForm ? 'Close' : 'New source'}
        </button>
      }
    >
      {noCategories && (
        <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          Create at least one category before adding a source.
        </div>
      )}

      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <div>
          <label className={labelClass} htmlFor="filter-cat">
            Filter by category
          </label>
          <select
            id="filter-cat"
            className={inputClass}
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option value="">All categories</option>
            {categories?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass} htmlFor="filter-active">
            Active state
          </label>
          <select
            id="filter-active"
            className={inputClass}
            value={filterActive}
            onChange={(e) => setFilterActive(e.target.value)}
          >
            <option value="">All</option>
            <option value="true">Active only</option>
            <option value="false">Disabled only</option>
          </select>
        </div>
      </div>

      {showForm && (
        <form
          onSubmit={onSubmit}
          className="mb-6 rounded-lg border border-gray-800 bg-gray-950/60 p-4"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="src-name">
                Name *
              </label>
              <input
                id="src-name"
                className={inputClass}
                value={form.name}
                maxLength={255}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. UK Plumbers Directory"
                required
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="src-cat">
                Category *
              </label>
              <select
                id="src-cat"
                className={inputClass}
                value={form.category_id}
                onChange={(e) =>
                  setForm({ ...form, category_id: e.target.value })
                }
                required
              >
                <option value="">Choose category…</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className={labelClass} htmlFor="src-url">
                URL pattern *
              </label>
              <input
                id="src-url"
                className={inputClass}
                value={form.url_pattern}
                onChange={(e) =>
                  setForm({ ...form, url_pattern: e.target.value })
                }
                placeholder="https://example.com/listings?page={page}"
                required
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="src-type">
                Scraping type *
              </label>
              <select
                id="src-type"
                className={inputClass}
                value={form.scraping_type}
                onChange={(e) =>
                  setForm({
                    ...form,
                    scraping_type: e.target.value as ScraperType,
                  })
                }
              >
                {SCRAPING_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass} htmlFor="src-platform">
                Platform
              </label>
              <select
                id="src-platform"
                className={inputClass}
                value={form.source_platform}
                onChange={(e) =>
                  setForm({
                    ...form,
                    source_platform: e.target.value as SourcePlatform,
                  })
                }
              >
                {PLATFORM_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass} htmlFor="src-postcode">
                Postcode prefix
              </label>
              <input
                id="src-postcode"
                className={inputClass}
                value={form.postcode_prefix}
                maxLength={16}
                onChange={(e) =>
                  setForm({ ...form, postcode_prefix: e.target.value })
                }
                placeholder="e.g. SW1 (optional; use {postcode} in URL)"
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="src-region">
                Region label
              </label>
              <input
                id="src-region"
                className={inputClass}
                value={form.region_label}
                maxLength={128}
                onChange={(e) =>
                  setForm({ ...form, region_label: e.target.value })
                }
                placeholder="e.g. Greater London (optional)"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(e) =>
                    setForm({ ...form, active: e.target.checked })
                  }
                  className="h-4 w-4 rounded border-gray-600 bg-gray-950 text-amber-500 focus:ring-amber-500"
                />
                Source is active
              </label>
            </div>
            <div className="md:col-span-2">
              <label className={labelClass} htmlFor="src-notes">
                Notes
              </label>
              <textarea
                id="src-notes"
                className={inputClass}
                rows={3}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Internal notes, e.g. rate limits, gotchas"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              className={buttonPrimaryClass}
              disabled={create.isPending || update.isPending}
            >
              {form.id ? 'Save changes' : 'Create source'}
            </button>
            <button
              type="button"
              className={buttonGhostClass}
              onClick={() => {
                setForm(EMPTY)
                setShowForm(false)
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Failed to load sources.
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Source</th>
              <th className="px-4 py-3 text-left font-semibold">Type</th>
              <th className="px-4 py-3 text-left font-semibold">Platform</th>
              <th className="px-4 py-3 text-left font-semibold">Geo</th>
              <th className="px-4 py-3 text-left font-semibold">Category</th>
              <th className="px-4 py-3 text-left font-semibold">Active</th>
              <th className="px-4 py-3 text-left font-semibold">Updated</th>
              <th className="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading &&
              [0, 1, 2].map((i) => (
                <tr key={i}>
                  <td colSpan={8} className="px-4 py-4">
                    <div className="h-5 animate-pulse rounded bg-gray-800" />
                  </td>
                </tr>
              ))}
            {!isLoading && data && data.length === 0 && (
              <EmptyRow colSpan={8} message="No sources match the current filters." />
            )}
            {data?.map((src) => (
              <tr key={src.id} className="hover:bg-gray-800/40">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-100">{src.name}</div>
                  <div className="mt-0.5 break-all text-xs text-gray-500">
                    {src.url_pattern}
                  </div>
                </td>
                <td className="px-4 py-3 text-xs uppercase tracking-wider text-gray-400">
                  {src.scraping_type}
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {src.source_platform?.replace('_', ' ') ?? '—'}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {src.postcode_prefix || src.region_label
                    ? [src.postcode_prefix, src.region_label].filter(Boolean).join(' · ')
                    : '—'}
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {categoryById.get(src.category_id)?.name || (
                    <span className="text-gray-500">unknown</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={
                      src.active
                        ? 'rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-300'
                        : 'rounded border border-gray-500/30 bg-gray-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400'
                    }
                  >
                    {src.active ? 'on' : 'off'}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {formatDate(src.updated_at)}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <button
                      type="button"
                      className={buttonGhostClass}
                      onClick={() => onEdit(src)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Edit
                    </button>
                    <button
                      type="button"
                      className={buttonDangerClass}
                      disabled={remove.isPending}
                      onClick={() => onDelete(src)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  )
}
