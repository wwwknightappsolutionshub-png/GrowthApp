'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Play, Plus, RefreshCw, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import {
  aiScraper,
  type AggressionLevel,
  type AiScraperCategory,
  type AiScraperSource,
  type AiScraperTaskRow,
  type TaskStatus,
} from '@/lib/api-client'
import {
  AggressionBadge,
  buttonDangerClass,
  buttonGhostClass,
  buttonPrimaryClass,
  EmptyRow,
  formatDate,
  inputClass,
  labelClass,
  SectionCard,
  StatusPill,
} from './shared'

const AGGRESSION_LEVELS: AggressionLevel[] = ['low', 'medium', 'high', 'extreme']
const STATUSES: TaskStatus[] = [
  'pending',
  'running',
  'paused',
  'completed',
  'error',
]

interface FormState {
  id: string | null
  source_id: string
  category_id: string
  aggression_level: AggressionLevel
  frequency: string
  status: TaskStatus
}

const EMPTY: FormState = {
  id: null,
  source_id: '',
  category_id: '',
  aggression_level: 'low',
  frequency: '0 * * * *',
  status: 'pending',
}

export function TasksPanel() {
  const qc = useQueryClient()
  const [form, setForm] = useState<FormState>(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [filterSource, setFilterSource] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  const { data: sources } = useQuery({
    queryKey: ['ai-scraper', 'sources', '', ''],
    queryFn: () => aiScraper.listSources().then((r) => r.data),
  })

  const { data: categories } = useQuery({
    queryKey: ['ai-scraper', 'categories'],
    queryFn: () => aiScraper.listCategories().then((r) => r.data),
  })

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['ai-scraper', 'tasks', filterSource, filterStatus],
    queryFn: () =>
      aiScraper
        .listTasks({
          source_id: filterSource || undefined,
          status: (filterStatus as TaskStatus) || undefined,
        })
        .then((r) => r.data),
  })

  const sourceById = useMemo(() => {
    const map = new Map<string, AiScraperSource>()
    sources?.forEach((s) => map.set(s.id, s))
    return map
  }, [sources])

  const categoryById = useMemo(() => {
    const map = new Map<string, AiScraperCategory>()
    categories?.forEach((c) => map.set(c.id, c))
    return map
  }, [categories])

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ['ai-scraper', 'tasks'] })

  const create = useMutation({
    mutationFn: () =>
      aiScraper.createTask({
        source_id: form.source_id,
        category_id: form.category_id,
        aggression_level: form.aggression_level,
        frequency: form.frequency.trim(),
        status: form.status,
      }),
    onSuccess: () => {
      toast.success('Task created')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to create task'),
  })

  const update = useMutation({
    mutationFn: () =>
      aiScraper.updateTask(form.id!, {
        source_id: form.source_id,
        category_id: form.category_id,
        aggression_level: form.aggression_level,
        frequency: form.frequency.trim(),
        status: form.status,
      }),
    onSuccess: () => {
      toast.success('Task updated')
      setForm(EMPTY)
      setShowForm(false)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to update task'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => aiScraper.deleteTask(id),
    onSuccess: () => {
      toast.success('Task deleted')
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to delete task'),
  })

  const run = useMutation({
    mutationFn: (id: string) => aiScraper.runTask(id),
    onSuccess: (res) => {
      toast.success(res.data.message)
      invalidate()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to run task'),
  })

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.source_id) {
      toast.error('Source is required')
      return
    }
    if (!form.category_id) {
      toast.error('Category is required')
      return
    }
    if (!form.frequency.trim()) {
      toast.error('Frequency is required')
      return
    }
    if (form.id) update.mutate()
    else create.mutate()
  }

  const onEdit = (task: AiScraperTaskRow) => {
    setForm({
      id: task.id,
      source_id: task.source_id,
      category_id: task.category_id,
      aggression_level: task.aggression_level,
      frequency: task.frequency,
      status: task.status,
    })
    setShowForm(true)
  }

  const onDelete = (task: AiScraperTaskRow) => {
    if (!confirm('Delete this scraper task?')) return
    remove.mutate(task.id)
  }

  const noSources = !sources || sources.length === 0
  const noCategories = !categories || categories.length === 0

  return (
    <SectionCard
      title="Tasks"
      description="Scheduled scraper jobs. Each task pairs a source with a category, cron, and aggression."
      actions={
        <div className="flex items-center gap-2">
          <button
            type="button"
            className={buttonGhostClass}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            type="button"
            className={buttonPrimaryClass}
            disabled={noSources || noCategories}
            onClick={() => {
              setForm(EMPTY)
              setShowForm((v) => !v)
            }}
          >
            {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            {showForm ? 'Close' : 'New task'}
          </button>
        </div>
      }
    >
      {(noSources || noCategories) && (
        <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          Create at least one source and one category before scheduling a task.
        </div>
      )}

      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <div>
          <label className={labelClass} htmlFor="task-filter-source">
            Filter by source
          </label>
          <select
            id="task-filter-source"
            className={inputClass}
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
          >
            <option value="">All sources</option>
            {sources?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass} htmlFor="task-filter-status">
            Filter by status
          </label>
          <select
            id="task-filter-status"
            className={inputClass}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
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
              <label className={labelClass} htmlFor="task-source">
                Source *
              </label>
              <select
                id="task-source"
                className={inputClass}
                value={form.source_id}
                onChange={(e) =>
                  setForm({ ...form, source_id: e.target.value })
                }
                required
              >
                <option value="">Choose source…</option>
                {sources?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass} htmlFor="task-cat">
                Category *
              </label>
              <select
                id="task-cat"
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
            <div>
              <label className={labelClass} htmlFor="task-aggr">
                Aggression level *
              </label>
              <select
                id="task-aggr"
                className={inputClass}
                value={form.aggression_level}
                onChange={(e) =>
                  setForm({
                    ...form,
                    aggression_level: e.target.value as AggressionLevel,
                  })
                }
              >
                {AGGRESSION_LEVELS.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                low ≈ 1 page · medium ≈ 5 · high ≈ 20 · extreme ≈ 60.
              </p>
            </div>
            <div>
              <label className={labelClass} htmlFor="task-status">
                Status
              </label>
              <select
                id="task-status"
                className={inputClass}
                value={form.status}
                onChange={(e) =>
                  setForm({ ...form, status: e.target.value as TaskStatus })
                }
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className={labelClass} htmlFor="task-cron">
                Cron expression (frequency) *
              </label>
              <input
                id="task-cron"
                className={inputClass}
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                placeholder="e.g. 0 * * * *"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                Standard 5-field cron (min hour day month weekday). 6 fields with
                seconds also accepted.
              </p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              className={buttonPrimaryClass}
              disabled={create.isPending || update.isPending}
            >
              {form.id ? 'Save changes' : 'Create task'}
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
          Failed to load tasks.
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Source</th>
              <th className="px-4 py-3 text-left font-semibold">Category</th>
              <th className="px-4 py-3 text-left font-semibold">Aggression</th>
              <th className="px-4 py-3 text-left font-semibold">Frequency</th>
              <th className="px-4 py-3 text-left font-semibold">Last run</th>
              <th className="px-4 py-3 text-left font-semibold">Next run</th>
              <th className="px-4 py-3 text-right font-semibold">Leads</th>
              <th className="px-4 py-3 text-left font-semibold">Status</th>
              <th className="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading &&
              [0, 1, 2].map((i) => (
                <tr key={i}>
                  <td colSpan={9} className="px-4 py-4">
                    <div className="h-5 animate-pulse rounded bg-gray-800" />
                  </td>
                </tr>
              ))}
            {!isLoading && data && data.length === 0 && (
              <EmptyRow colSpan={9} message="No tasks scheduled yet." />
            )}
            {data?.map((task) => (
              <tr key={task.id} className="hover:bg-gray-800/40">
                <td className="px-4 py-3 font-medium text-gray-100">
                  {sourceById.get(task.source_id)?.name || (
                    <span className="text-gray-500">unknown</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {categoryById.get(task.category_id)?.name || (
                    <span className="text-gray-500">unknown</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <AggressionBadge level={task.aggression_level} />
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-300">
                  {task.frequency}
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {formatDate(task.last_run)}
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {formatDate(task.next_run)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-emerald-300">
                  {task.total_leads_extracted}
                </td>
                <td className="px-4 py-3">
                  <StatusPill status={task.status} />
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <button
                      type="button"
                      className={buttonGhostClass}
                      disabled={run.isPending || task.status === 'running'}
                      onClick={() => run.mutate(task.id)}
                    >
                      <Play className="h-3.5 w-3.5" />
                      Run
                    </button>
                    <button
                      type="button"
                      className={buttonGhostClass}
                      onClick={() => onEdit(task)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Edit
                    </button>
                    <button
                      type="button"
                      className={buttonDangerClass}
                      disabled={remove.isPending}
                      onClick={() => onDelete(task)}
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
