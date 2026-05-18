'use client'

import { useState } from 'react'
import { BillingTable, type BillingTableColumn } from './BillingTable'

export interface AuditRow {
  id: string
  timestamp: string | null
  type: 'plan_change' | 'overage_flag' | 'invoice_event' | 'payment_failure' | 'other'
  entity_type: 'tenant' | 'freelancer' | 'system'
  entity_id: string | null
  entity_name: string | null
  description: string
  metadata: Record<string, unknown>
}

const TYPE_STYLES: Record<AuditRow['type'], string> = {
  plan_change: 'bg-blue-500/15 text-blue-300',
  overage_flag: 'bg-amber-500/15 text-amber-300',
  invoice_event: 'bg-emerald-500/15 text-emerald-300',
  payment_failure: 'bg-red-500/15 text-red-300',
  other: 'bg-gray-500/15 text-gray-300',
}

export function AuditLogTable({
  rows,
  isLoading,
  isError,
}: {
  rows: AuditRow[]
  isLoading?: boolean
  isError?: boolean
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const columns: BillingTableColumn<AuditRow>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp',
      render: (r) => (
        <span className="text-xs text-gray-300">
          {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (r) => (
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest ${TYPE_STYLES[r.type]}`}
        >
          {r.type.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'entity',
      header: 'Entity',
      render: (r) => (
        <div>
          <div className="text-xs text-gray-200">{r.entity_name ?? '—'}</div>
          <div className="text-[10px] uppercase tracking-widest text-gray-500">{r.entity_type}</div>
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (r) => <span className="text-sm text-gray-200">{r.description}</span>,
    },
    {
      key: 'metadata',
      header: 'Metadata',
      render: (r) => {
        const open = expanded[r.id]
        const hasMeta = r.metadata && Object.keys(r.metadata).length > 0
        if (!hasMeta) return <span className="text-xs text-gray-600">—</span>
        return (
          <div>
            <button
              onClick={() => setExpanded((s) => ({ ...s, [r.id]: !open }))}
              className="text-xs text-amber-400 hover:underline"
            >
              {open ? 'Hide JSON' : 'View JSON'}
            </button>
            {open ? (
              <pre className="mt-1 max-h-48 overflow-auto rounded border border-gray-800 bg-gray-950 p-2 text-[10px] text-gray-400">
                {JSON.stringify(r.metadata, null, 2)}
              </pre>
            ) : null}
          </div>
        )
      },
    },
  ]

  return <BillingTable rows={rows} columns={columns} rowKey={(r) => r.id} isLoading={isLoading} isError={isError} />
}
