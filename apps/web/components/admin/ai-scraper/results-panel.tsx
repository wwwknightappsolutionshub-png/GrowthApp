'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, RefreshCw } from 'lucide-react'

import {
  aiScraper,
  type AiScraperResult,
  type AiScraperTaskRow,
} from '@/lib/api-client'
import {
  buttonGhostClass,
  EmptyRow,
  formatDate,
  inputClass,
  labelClass,
  SectionCard,
} from './shared'

export function ResultsPanel() {
  const [filterTask, setFilterTask] = useState('')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const { data: tasks } = useQuery({
    queryKey: ['ai-scraper', 'tasks', '', ''],
    queryFn: () => aiScraper.listTasks().then((r) => r.data),
  })

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['ai-scraper', 'results', filterTask],
    queryFn: () =>
      aiScraper
        .listResults({ task_id: filterTask || undefined, limit: 100 })
        .then((r) => r.data),
  })

  const taskById = useMemo(() => {
    const map = new Map<string, AiScraperTaskRow>()
    tasks?.forEach((t) => map.set(t.id, t))
    return map
  }, [tasks])

  const toggle = (id: string) =>
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))

  return (
    <SectionCard
      title="Results"
      description="The 100 most recent scraper outputs, including extracted JSON and quality scores."
      actions={
        <button
          type="button"
          className={buttonGhostClass}
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      }
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <div>
          <label className={labelClass} htmlFor="result-filter">
            Filter by task
          </label>
          <select
            id="result-filter"
            className={inputClass}
            value={filterTask}
            onChange={(e) => setFilterTask(e.target.value)}
          >
            <option value="">All tasks</option>
            {tasks?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.id.slice(0, 8)}… ({t.aggression_level} · {t.frequency})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Failed to load results.
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="w-10 px-4 py-3 text-left font-semibold"></th>
              <th className="px-4 py-3 text-left font-semibold">When</th>
              <th className="px-4 py-3 text-left font-semibold">Task</th>
              <th className="px-4 py-3 text-right font-semibold">AI score</th>
              <th className="px-4 py-3 text-right font-semibold">New leads</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading &&
              [0, 1, 2].map((i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-4 py-4">
                    <div className="h-5 animate-pulse rounded bg-gray-800" />
                  </td>
                </tr>
              ))}
            {!isLoading && data && data.length === 0 && (
              <EmptyRow colSpan={5} message="No scraper results recorded yet." />
            )}
            {data?.map((row) => (
              <ResultRow
                key={row.id}
                row={row}
                expanded={!!expanded[row.id]}
                onToggle={() => toggle(row.id)}
                taskLabel={taskLabel(row, taskById)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  )
}

function taskLabel(
  row: AiScraperResult,
  map: Map<string, AiScraperTaskRow>,
): string {
  const t = map.get(row.task_id)
  if (!t) return row.task_id.slice(0, 8) + '…'
  return `${t.aggression_level} · ${t.frequency} (${row.task_id.slice(0, 8)}…)`
}

function ResultRow({
  row,
  expanded,
  onToggle,
  taskLabel,
}: {
  row: AiScraperResult
  expanded: boolean
  onToggle: () => void
  taskLabel: string
}) {
  return (
    <>
      <tr className="cursor-pointer hover:bg-gray-800/40" onClick={onToggle}>
        <td className="px-4 py-3 text-gray-500">
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </td>
        <td className="px-4 py-3 text-xs text-gray-400">
          {formatDate(row.created_at)}
        </td>
        <td className="px-4 py-3 text-xs text-gray-300">{taskLabel}</td>
        <td className="px-4 py-3 text-right">
          <ScorePill score={row.ai_score} />
        </td>
        <td className="px-4 py-3 text-right tabular-nums text-emerald-300">
          {row.new_leads_created}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-gray-950/60">
          <td colSpan={5} className="px-4 py-4">
            <div className="grid gap-4 md:grid-cols-2">
              <PayloadBlock title="AI extracted data" data={row.ai_extracted_data} />
              <PayloadBlock title="Cleaned payload" data={row.cleaned_payload} />
            </div>
            {row.raw_payload && (
              <details className="mt-4 rounded border border-gray-800 bg-gray-950 p-3">
                <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Raw payload ({row.raw_payload.length.toLocaleString()} chars)
                </summary>
                <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all text-[11px] leading-relaxed text-gray-400">
                  {row.raw_payload.slice(0, 5000)}
                  {row.raw_payload.length > 5000 ? '\n…truncated' : ''}
                </pre>
              </details>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

function PayloadBlock({
  title,
  data,
}: {
  title: string
  data: Record<string, unknown>
}) {
  const json = JSON.stringify(data, null, 2)
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
        {title}
      </div>
      <pre className="max-h-64 overflow-auto rounded border border-gray-800 bg-gray-950 p-3 text-[11px] leading-relaxed text-gray-300">
        {json === '{}' ? '— empty —' : json}
      </pre>
    </div>
  )
}

function ScorePill({ score }: { score: number }) {
  const tone =
    score >= 80
      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      : score >= 50
      ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
      : 'bg-gray-500/15 text-gray-400 border-gray-500/30'
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold tabular-nums ${tone}`}
    >
      {score}
    </span>
  )
}
