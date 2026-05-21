'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Calendar, ExternalLink, Sparkles, X, Zap } from 'lucide-react'
import { toast } from 'sonner'
import { crm, leads } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'
import { CrmEntityTimeline } from '@/components/crm/CrmEntityTimeline'

type BoardCard = {
  card_type: 'lead' | 'deal'
  id: string
  title: string
  email?: string | null
  customer_name?: string | null
}

export function CrmBoardCardPanel({
  card,
  onClose,
}: {
  card: BoardCard
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [note, setNote] = useState('')
  const isLead = card.card_type === 'lead'
  const entityType = card.card_type

  const { data: leadDetail } = useQuery({
    queryKey: ['lead', card.id],
    queryFn: () => leads.get(card.id).then((r) => r.data),
    enabled: isLead,
  })

  const { data: dealDetail } = useQuery({
    queryKey: ['crm', 'deal', card.id],
    queryFn: () => crm.getDeal(card.id).then((r) => r.data),
    enabled: !isLead,
  })

  const { data: bookings } = useQuery({
    queryKey: ['crm', card.card_type, card.id, 'bookings'],
    queryFn: () =>
      isLead
        ? crm.leadBookings(card.id).then((r) => r.data)
        : crm.dealBookings(card.id).then((r) => r.data),
  })

  const enrichMut = useMutation({
    mutationFn: () => crm.enrichLead(card.id),
    onSuccess: (res) => {
      toast.success('Lead enriched')
      qc.invalidateQueries({ queryKey: ['crm', 'timeline', 'lead', card.id] })
      if (res.data?.summary) {
        toast.message(res.data.summary.slice(0, 120))
      }
    },
    onError: () => toast.error('Enrichment failed'),
  })

  const addNote = useMutation({
    mutationFn: () =>
      crm.createActivity({
        entity_type: entityType,
        entity_id: card.id,
        activity_type: 'note',
        body: note,
      }),
    onSuccess: () => {
      toast.success('Note added')
      setNote('')
      qc.invalidateQueries({ queryKey: ['crm', 'timeline', entityType, card.id] })
    },
  })

  const aiSummary = isLead ? leadDetail?.extra_data?.ai_summary : undefined

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background shadow-xl">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <p className="text-xs font-bold uppercase text-muted-foreground">{isLead ? 'Lead' : 'Deal'}</p>
          <h2 className="font-semibold text-foreground">{card.title}</h2>
        </div>
        <button type="button" onClick={onClose} className="rounded-lg p-1 hover:bg-muted">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto p-4">
        {isLead && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={enrichMut.isPending}
              onClick={() => enrichMut.mutate()}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              {enrichMut.isPending ? 'Enriching…' : 'AI enrich'}
            </button>
            <button
              type="button"
              onClick={() => crm.applyLeadScores(card.id).then(() => toast.success('Scores applied'))}
              className="rounded-lg border border-border px-3 py-2 text-sm font-medium"
            >
              Apply scores
            </button>
          </div>
        )}

        {aiSummary && (
          <p className="rounded-lg border border-brand-teal-300/40 bg-brand-teal-500/5 px-3 py-2 text-sm text-foreground">
            {aiSummary}
          </p>
        )}

        {!isLead && dealDetail?.customer_id && (
          <Link
            href={`/dashboard/crm/customers/${dealDetail.customer_id}`}
            className="inline-flex items-center gap-1 text-sm text-brand-teal-600 hover:underline"
          >
            View customer <ExternalLink className="h-3.5 w-3.5" />
          </Link>
        )}

        <div>
          <h3 className="mb-2 text-sm font-semibold text-foreground">Activity timeline</h3>
          <div className="mb-3 flex gap-2">
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note…"
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={!note.trim() || addNote.isPending}
              onClick={() => addNote.mutate()}
              className="rounded-lg bg-brand-forest-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              Add
            </button>
          </div>
          <CrmEntityTimeline entityType={entityType} entityId={card.id} />
        </div>

        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-foreground">
            <Calendar className="h-4 w-4" /> Appointments (read-only)
          </h3>
          {(bookings ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No linked bookings</p>
          ) : (
            <ul className="space-y-2">
              {(bookings as { id: string; booking_date?: string; status: string; service_type?: string }[]).map(
                (b) => (
                  <li key={b.id} className="rounded-lg border border-border px-3 py-2 text-sm">
                    <p className="font-medium">{b.service_type || 'Booking'}</p>
                    <p className="text-muted-foreground">
                      {b.booking_date ? formatDate(b.booking_date) : '—'} · {b.status}
                    </p>
                  </li>
                ),
              )}
            </ul>
          )}
        </div>

        <Link
          href="/dashboard/automations"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <Zap className="h-4 w-4" />
          Configure automations for stage changes
        </Link>
      </div>
    </div>
  )
}
