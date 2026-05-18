'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useDroppable } from '@dnd-kit/core'
import { Calendar, Filter, Flag, LayoutGrid, List, Plus, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { tasks as tasksApi } from '@/lib/api-client'

type Task = {
  id: string
  title: string
  description: string | null
  status: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
  position: number
  labels: string[]
  due_at: string | null
  reminder_at: string | null
  assigned_user_id: string | null
  created_at: string
}

type BoardColumn = { status: string; label: string; items: Task[] }
type Board = { columns: BoardColumn[] }

const PRIORITY_STYLES: Record<Task['priority'], string> = {
  low: 'bg-gray-100 text-muted-foreground',
  normal: 'bg-brand-teal-400/20 text-brand-teal-100',
  high: 'bg-amber-100 text-amber-800',
  urgent: 'bg-red-100 text-red-700',
}

const COLUMN_STYLES: Record<string, string> = {
  todo: 'bg-brand-forest-950 border-brand-forest-800',
  doing: 'bg-brand-forest-900 border-brand-forest-700',
  blocked: 'bg-amber-950/50 border-amber-400/30',
  done: 'bg-brand-teal-950/40 border-brand-teal-400/30',
}

function dueLabel(iso: string | null): { text: string; tint: string } | null {
  if (!iso) return null
  const due = new Date(iso).getTime()
  const now = Date.now()
  const diff = due - now
  const days = Math.floor(diff / 86_400_000)
  if (diff < 0) return { text: 'Overdue', tint: 'text-red-600 bg-red-50' }
  if (days === 0) return { text: 'Due today', tint: 'text-amber-700 bg-amber-50' }
  if (days < 7) return { text: `Due in ${days}d`, tint: 'text-muted-foreground bg-gray-100' }
  return { text: new Date(iso).toLocaleDateString(), tint: 'text-muted-foreground bg-gray-100' }
}

function TaskCard({ task, onOpen }: { task: Task; onOpen: (t: Task) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: task.id })
  const due = dueLabel(task.due_at)
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      {...attributes}
      {...listeners}
      onDoubleClick={() => onOpen(task)}
      className={`group bg-brand-forest-900 rounded-lg border border-brand-forest-700 p-3 cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md hover:border-brand-teal-300 transition-all ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-white leading-snug line-clamp-3">{task.title}</p>
        <span
          className={`text-[10px] font-bold uppercase tracking-wide rounded px-1.5 py-0.5 flex-shrink-0 ${PRIORITY_STYLES[task.priority]}`}
        >
          {task.priority === 'normal' ? 'med' : task.priority}
        </span>
      </div>

      {task.labels && task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {task.labels.slice(0, 3).map((label) => (
            <span key={label} className="text-[10px] bg-brand-teal-400/20 text-brand-teal-100 px-1.5 py-0.5 rounded">
              {label}
            </span>
          ))}
        </div>
      )}

      {due && (
        <div className={`mt-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${due.tint}`}>
          <Calendar className="w-3 h-3" />
          {due.text}
        </div>
      )}
    </div>
  )
}

function Column({
  column,
  onOpen,
}: {
  column: BoardColumn
  onOpen: (t: Task) => void
}) {
  const { setNodeRef } = useDroppable({ id: `col:${column.status}` })
  return (
    <div
      ref={setNodeRef}
      className={`w-[min(18rem,82vw)] flex-shrink-0 snap-start rounded-xl border-2 p-3 ${COLUMN_STYLES[column.status] ?? 'bg-brand-forest-950 border-brand-forest-800'}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">{column.label}</h3>
        <span className="text-xs bg-brand-forest-800 rounded-full px-2 py-0.5 font-medium text-brand-teal-100/70 shadow-sm">
          {column.items.length}
        </span>
      </div>
      <SortableContext items={column.items.map((t) => t.id)} strategy={verticalListSortingStrategy} id={column.status}>
        <div className="space-y-2 min-h-32">
          {column.items.map((task) => (
            <TaskCard key={task.id} task={task} onOpen={onOpen} />
          ))}
        </div>
      </SortableContext>
    </div>
  )
}

function NewTaskModal({
  open,
  initialStatus,
  onClose,
  onCreated,
}: {
  open: boolean
  initialStatus: string
  onClose: () => void
  onCreated: () => void
}) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<Task['priority']>('normal')
  const [status, setStatus] = useState(initialStatus)
  const [dueAt, setDueAt] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const reset = () => {
    setTitle('')
    setDescription('')
    setPriority('normal')
    setDueAt('')
    setStatus(initialStatus)
  }

  const submit = async () => {
    if (!title.trim()) return
    setSubmitting(true)
    try {
      await tasksApi.create({
        title: title.trim(),
        description: description.trim() || null,
        priority,
        status,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
      })
      toast.success('Task created')
      reset()
      onCreated()
      onClose()
    } catch (err) {
      toast.error('Failed to create task')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-gray-950/60"
      />
      <div className="relative w-full max-w-md bg-card rounded-xl shadow-2xl">
        <header className="flex items-center justify-between px-5 py-4 border-b border-border/50">
          <h2 className="text-base font-bold text-foreground">New task</h2>
          <button type="button" onClick={onClose} className="p-1 text-gray-400 hover:text-foreground/80">
            <X className="w-4 h-4" />
          </button>
        </header>
        <div className="p-5 space-y-3">
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Title</label>
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30"
              placeholder="What needs doing?"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30 resize-y"
              placeholder="Notes, context, link to a deal…"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="mt-1 w-full px-2 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30"
              >
                <option value="todo">To do</option>
                <option value="doing">In progress</option>
                <option value="blocked">Blocked</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as Task['priority'])}
                className="mt-1 w-full px-2 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground">Due</label>
              <input
                type="datetime-local"
                value={dueAt}
                onChange={(e) => setDueAt(e.target.value)}
                className="mt-1 w-full px-2 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30"
              />
            </div>
          </div>
        </div>
        <footer className="flex items-center justify-end gap-2 px-5 py-3 bg-brand-forest-950 border-t border-border/50 rounded-b-xl">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting || !title.trim()}
            className="px-4 py-1.5 text-sm font-semibold text-brand-forest-foreground bg-brand-forest-700 rounded-lg hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create task'}
          </button>
        </footer>
      </div>
    </div>
  )
}

export default function TasksPage() {
  const qc = useQueryClient()
  const [activeId, setActiveId] = useState<string | null>(null)
  const [view, setView] = useState<'board' | 'list'>('board')
  const [showNew, setShowNew] = useState(false)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))

  const { data, isLoading } = useQuery<Board>({
    queryKey: ['tasks-board'],
    queryFn: () => tasksApi.board().then((r) => r.data),
  })

  const moveMutation = useMutation({
    mutationFn: ({ id, status, position }: { id: string; status: string; position: number }) =>
      tasksApi.move(id, status, position),
    onMutate: async ({ id, status, position }) => {
      await qc.cancelQueries({ queryKey: ['tasks-board'] })
      const prev = qc.getQueryData<Board>(['tasks-board'])
      if (!prev) return { prev }
      const next: Board = { columns: prev.columns.map((c) => ({ ...c, items: [...c.items] })) }
      let moving: Task | undefined
      for (const col of next.columns) {
        const idx = col.items.findIndex((t) => t.id === id)
        if (idx >= 0) {
          moving = col.items.splice(idx, 1)[0]
          break
        }
      }
      if (moving) {
        const target = next.columns.find((c) => c.status === status)
        if (target) {
          moving.status = status
          target.items.splice(position, 0, moving)
        }
      }
      qc.setQueryData(['tasks-board'], next)
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(['tasks-board'], ctx.prev)
      toast.error('Failed to move task')
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['tasks-board'] }),
  })

  const flatTasks: Task[] = useMemo(
    () => data?.columns.flatMap((c) => c.items) ?? [],
    [data],
  )
  const activeTask = activeId ? flatTasks.find((t) => t.id === activeId) ?? null : null

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveId(null)
    if (!over) return
    const sourceCol = data?.columns.find((c) => c.items.some((t) => t.id === active.id))
    if (!sourceCol) return

    const overId = String(over.id)
    let targetStatus: string | undefined
    let targetPosition = 0

    if (overId.startsWith('col:')) {
      targetStatus = overId.slice(4)
      const tc = data?.columns.find((c) => c.status === targetStatus)
      targetPosition = tc?.items.length ?? 0
    } else {
      const targetCol = data?.columns.find((c) => c.items.some((t) => t.id === overId))
      if (!targetCol) return
      targetStatus = targetCol.status
      targetPosition = targetCol.items.findIndex((t) => t.id === overId)
    }

    if (!targetStatus) return
    if (active.id === overId && sourceCol.status === targetStatus) return

    moveMutation.mutate({
      id: String(active.id),
      status: targetStatus,
      position: Math.max(0, targetPosition),
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Tasks</h1>
          <p className="text-muted-foreground text-sm">
            {flatTasks.length} task{flatTasks.length === 1 ? '' : 's'} across {data?.columns.length ?? 4} columns
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-border bg-card overflow-hidden">
            <button
              type="button"
              onClick={() => setView('board')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium ${
                view === 'board' ? 'bg-brand-forest-700 text-brand-forest-foreground' : 'text-muted-foreground hover:bg-brand-forest-50'
              }`}
            >
              <LayoutGrid className="w-4 h-4" /> Board
            </button>
            <button
              type="button"
              onClick={() => setView('list')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border-l border-border ${
                view === 'list' ? 'bg-brand-forest-700 text-brand-forest-foreground' : 'text-muted-foreground hover:bg-brand-forest-50'
              }`}
            >
              <List className="w-4 h-4" /> List
            </button>
          </div>
          <button
            type="button"
            onClick={() => setShowNew(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold text-brand-forest-foreground bg-brand-forest-700 rounded-lg hover:bg-brand-forest-800"
          >
            <Plus className="w-4 h-4" /> New task
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      )}

      {!isLoading && view === 'board' && data && (
        <DndContext
          sensors={sensors}
          onDragStart={(e) => setActiveId(String(e.active.id))}
          onDragCancel={() => setActiveId(null)}
          onDragEnd={handleDragEnd}
        >
          <div className="flex snap-x gap-4 overflow-x-auto pb-4">
            {data.columns.map((col) => (
              <Column key={col.status} column={col} onOpen={() => null} />
            ))}
          </div>
          <DragOverlay>
            {activeTask && (
              <div className="bg-brand-forest-900 rounded-lg border border-brand-forest-700 p-3 shadow-2xl w-72">
                <p className="text-sm font-medium text-foreground">{activeTask.title}</p>
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}

      {!isLoading && view === 'list' && data && (
        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 divide-y divide-brand-forest-800">
          {flatTasks.length === 0 && (
            <div className="px-6 py-12 text-center text-sm text-brand-teal-100/60">No tasks yet.</div>
          )}
          {flatTasks.map((t) => {
            const due = dueLabel(t.due_at)
            return (
              <div key={t.id} className="flex items-center gap-3 px-4 py-3">
                <Flag className={`w-4 h-4 ${PRIORITY_STYLES[t.priority]}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{t.title}</p>
                  <p className="text-xs text-muted-foreground">{t.status}</p>
                </div>
                {due && (
                  <span className={`text-[11px] px-1.5 py-0.5 rounded ${due.tint}`}>{due.text}</span>
                )}
              </div>
            )
          })}
        </div>
      )}

      <NewTaskModal
        open={showNew}
        initialStatus="todo"
        onClose={() => setShowNew(false)}
        onCreated={() => qc.invalidateQueries({ queryKey: ['tasks-board'] })}
      />
    </div>
  )
}
