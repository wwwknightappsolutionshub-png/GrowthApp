'use client'

import { useQuery } from '@tanstack/react-query'
import { Mail, MessageSquare, Sparkles, Zap } from 'lucide-react'
import { crm } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'

export type TimelineItem = {
  id: string
  source: string
  activity_type: string
  title?: string | null
  body?: string | null
  channel?: string | null
  direction?: string | null
  created_at: string
}

function iconFor(item: TimelineItem) {
  if (item.source === 'automation') return Zap
  if (item.source === 'message') return item.channel === 'email' ? Mail : MessageSquare
  if (item.activity_type === 'ai_enrichment') return Sparkles
  return MessageSquare
}

function labelFor(item: TimelineItem) {
  if (item.source === 'automation') return 'Automation'
  if (item.source === 'message') {
    const dir = item.direction === 'inbound' ? 'Received' : 'Sent'
    return `${dir} ${item.channel ?? 'message'}`
  }
  if (item.activity_type === 'ai_enrichment') return 'AI enrichment'
  return item.activity_type.replace(/_/g, ' ')
}

export function CrmEntityTimeline({
  entityType,
  entityId,
}: {
  entityType: string
  entityId: string
}) {
  const { data: items, isLoading } = useQuery({
    queryKey: ['crm', 'timeline', entityType, entityId],
    queryFn: () => crm.getTimeline(entityType, entityId).then((r) => r.data as TimelineItem[]),
    enabled: !!entityId,
  })

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading timeline…</p>
  }

  if (!items?.length) {
    return <p className="text-sm text-muted-foreground">No activity yet</p>
  }

  return (
    <ul className="max-h-80 space-y-3 overflow-y-auto">
      {items.map((item) => {
        const Icon = iconFor(item)
        return (
          <li key={item.id} className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
            <div className="flex items-center gap-2">
              <Icon className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase text-muted-foreground">
                {labelFor(item)}
              </span>
              {item.title && (
                <span className="truncate text-xs text-foreground">· {item.title}</span>
              )}
            </div>
            <p className="mt-1 text-foreground">{item.body || '—'}</p>
            <p className="mt-1 text-xs text-muted-foreground">{formatDate(item.created_at)}</p>
          </li>
        )
      })}
    </ul>
  )
}
