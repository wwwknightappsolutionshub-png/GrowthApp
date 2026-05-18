'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import { aiScraper, type AiScraperCategory } from '@/lib/api-client'
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

interface FormState {
  id: string | null
  name: string
  description: string
}

const EMPTY: FormState = { id: null, name: '', description: '' }

export function CategoriesPanel() {
  const qc = useQueryClient()
  const [form, setForm] = useState<FormState>(EMPTY)
  const [showForm, setShowForm] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['ai-scraper', 'categories'],
    queryFn: () => aiScraper.listCategories().then((r) => r.data),
  })

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ['ai-scraper', 'categories'] })

  const create = useMutation({
    mutationFn: () =>
      aiScraper.createCategory({
        name: form.name.trim(),
        description: form.description.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Category created')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to create category'),
  })

  const update = useMutation({
    mutationFn: () =>
      aiScraper.updateCategory(form.id!, {
        name: form.name.trim() || undefined,
        description: form.description.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Category updated')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to update category'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => aiScraper.deleteCategory(id),
    onSuccess: () => {
      toast.success('Category deleted')
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to delete category'),
  })

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.name.trim()) {
      toast.error('Name is required')
      return
    }
    if (form.id) update.mutate()
    else create.mutate()
  }

  const onEdit = (cat: AiScraperCategory) => {
    setForm({ id: cat.id, name: cat.name, description: cat.description ?? '' })
    setShowForm(true)
  }

  const onDelete = (cat: AiScraperCategory) => {
    if (!confirm(`Delete category "${cat.name}"? This cannot be undone.`)) return
    remove.mutate(cat.id)
  }

  return (
    <SectionCard
      title="Categories"
      description="Industry buckets used to organise scraper sources and lead routing."
      actions={
        <button
          type="button"
          className={buttonPrimaryClass}
          onClick={() => {
            setForm(EMPTY)
            setShowForm((v) => !v)
          }}
        >
          {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {showForm ? 'Close' : 'New category'}
        </button>
      }
    >
      {showForm && (
        <form
          onSubmit={onSubmit}
          className="mb-6 rounded-lg border border-gray-800 bg-gray-950/60 p-4"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="cat-name">
                Name *
              </label>
              <input
                id="cat-name"
                className={inputClass}
                value={form.name}
                maxLength={160}
                placeholder="e.g. Tradesmen, SaaS founders"
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="cat-desc">
                Description
              </label>
              <input
                id="cat-desc"
                className={inputClass}
                value={form.description}
                placeholder="Optional notes"
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              className={buttonPrimaryClass}
              disabled={create.isPending || update.isPending}
            >
              {form.id ? 'Save changes' : 'Create category'}
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
          Failed to load categories.
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Name</th>
              <th className="px-4 py-3 text-left font-semibold">Description</th>
              <th className="px-4 py-3 text-left font-semibold">Created</th>
              <th className="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading &&
              [0, 1, 2].map((i) => (
                <tr key={i}>
                  <td colSpan={4} className="px-4 py-4">
                    <div className="h-5 animate-pulse rounded bg-gray-800" />
                  </td>
                </tr>
              ))}
            {!isLoading && data && data.length === 0 && (
              <EmptyRow colSpan={4} message="No categories yet. Create one to get started." />
            )}
            {data?.map((cat) => (
              <tr key={cat.id} className="hover:bg-gray-800/40">
                <td className="px-4 py-3 font-medium text-gray-100">{cat.name}</td>
                <td className="px-4 py-3 text-gray-400">
                  {cat.description || <span className="text-gray-600">—</span>}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {formatDate(cat.created_at)}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <button
                      type="button"
                      className={buttonGhostClass}
                      onClick={() => onEdit(cat)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Edit
                    </button>
                    <button
                      type="button"
                      className={buttonDangerClass}
                      disabled={remove.isPending}
                      onClick={() => onDelete(cat)}
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
