'use client'

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export const inputClass =
  'w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-600 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/30 disabled:opacity-60'

export const labelClass = 'mb-1 block text-xs font-medium text-gray-400'

export const buttonPrimaryClass =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed'

export const buttonGhostClass =
  'inline-flex items-center gap-1.5 rounded-md border border-gray-700 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 disabled:opacity-50'

export const buttonDangerClass =
  'inline-flex items-center gap-1.5 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/20 disabled:opacity-50'

export function SectionCard({
  title,
  description,
  actions,
  children,
}: {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-gray-100">{title}</h2>
          {description && (
            <p className="mt-0.5 text-xs text-gray-400">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <div className="p-5">{children}</div>
    </section>
  )
}

export function EmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-5 py-10 text-center text-sm text-gray-500">
        {message}
      </td>
    </tr>
  )
}

export function StatusPill({
  status,
}: {
  status: 'pending' | 'running' | 'paused' | 'completed' | 'error' | string
}) {
  const tones: Record<string, string> = {
    pending: 'bg-gray-500/15 text-gray-300 border-gray-500/30',
    running: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    paused: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    error: 'bg-red-500/15 text-red-300 border-red-500/30',
  }
  const tone = tones[status] || tones.pending
  return (
    <span
      className={cn(
        'inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
        tone,
      )}
    >
      {status}
    </span>
  )
}

export function AggressionBadge({ level }: { level: string }) {
  const tones: Record<string, string> = {
    low: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    medium: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    high: 'bg-orange-500/10 text-orange-300 border-orange-500/30',
    extreme: 'bg-red-500/10 text-red-300 border-red-500/30',
  }
  const tone = tones[level] || tones.low
  return (
    <span
      className={cn(
        'inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
        tone,
      )}
    >
      {level}
    </span>
  )
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}
