'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { toast } from 'sonner'
import { crm } from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'
import { Loader2 } from 'lucide-react'
import { CrmBoardCardPanel } from '@/components/crm/CrmBoardCardPanel'

type BoardCard = {
  card_type: 'lead' | 'deal'
  id: string
  title: string
  stage_order: number
  email?: string | null
  phone?: string | null
  source?: string | null
  score?: number | null
  score_label?: string | null
  customer_name?: string | null
  value_pence?: number
  stage?: string
}

function cardKey(c: BoardCard) {
  return `${c.card_type}:${c.id}`
}

function BoardCardItem({
  card,
  onOpen,
}: {
  card: BoardCard
  onOpen: (card: BoardCard) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: cardKey(card),
  })
  const isLead = card.card_type === 'lead'

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      {...attributes}
      {...listeners}
      role="button"
      tabIndex={0}
      onClick={() => onOpen(card)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onOpen(card)
      }}
      className={`cursor-grab rounded-lg border bg-card p-3 shadow-sm active:cursor-grabbing hover:shadow-md ${
        isDragging ? 'opacity-50' : ''
      } ${isLead ? 'border-blue-200/80 dark:border-blue-800' : 'border-border'}`}
    >
      <div className="mb-1 flex items-center justify-between gap-1">
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
            isLead
              ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'
              : 'bg-brand-teal-500/15 text-brand-teal-700 dark:text-brand-teal-300'
          }`}
        >
          {isLead ? 'Lead' : 'Deal'}
        </span>
        {isLead && card.score != null && (
          <span className="text-[10px] font-semibold text-muted-foreground">{card.score}</span>
        )}
      </div>
      <p className="truncate text-sm font-medium text-foreground">{card.title}</p>
      {!isLead && card.customer_name && (
        <p className="mt-0.5 truncate text-xs text-muted-foreground">{card.customer_name}</p>
      )}
      {isLead && card.source && (
        <p className="mt-0.5 truncate text-xs text-muted-foreground">{card.source}</p>
      )}
      {!isLead && (card.value_pence ?? 0) > 0 && (
        <p className="mt-2 text-xs font-semibold text-brand-teal-600">
          {formatCurrency(card.value_pence!)}
        </p>
      )}
    </div>
  )
}

export function UnifiedPipelineBoard() {
  const qc = useQueryClient()
  const [pipelineId, setPipelineId] = useState<string | undefined>(undefined)
  const [selectedCard, setSelectedCard] = useState<BoardCard | null>(null)

  const { data: pipelines } = useQuery({
    queryKey: ['crm', 'pipelines'],
    queryFn: () => crm.listPipelines().then((r) => r.data),
  })

  const activePipelineId = pipelineId ?? pipelines?.[0]?.id

  const { data: board, isLoading } = useQuery({
    queryKey: ['crm', 'board', activePipelineId],
    queryFn: () => crm.getBoard(activePipelineId).then((r) => r.data),
    enabled: !!activePipelineId,
  })

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const moveMut = useMutation({
    mutationFn: (payload: { card_type: string; card_id: string; stage_id: string; stage_order: number }) =>
      crm.moveBoardCard(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['crm', 'board'] })
      qc.invalidateQueries({ queryKey: ['crm', 'dashboard'] })
    },
    onError: () => toast.error('Failed to move card'),
  })

  const stageIds = useMemo(
    () => (board?.columns ?? []).map((col: { stage: { id: string } }) => col.stage.id),
    [board],
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || !board) return

    const activeKey = String(active.id)
    const overId = String(over.id)

    let targetStageId: string | null = null
    if (stageIds.includes(overId)) {
      targetStageId = overId
    } else {
      for (const col of board.columns) {
        const all = [...(col.leads ?? []), ...(col.deals ?? [])]
        if (all.some((c: BoardCard) => cardKey(c) === overId)) {
          targetStageId = col.stage.id
          break
        }
      }
    }
    if (!targetStageId) return

    const [cardType, cardId] = activeKey.split(':')
    if (!cardType || !cardId) return

    moveMut.mutate({
      card_type: cardType,
      card_id: cardId,
      stage_id: targetStageId,
      stage_order: 0,
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-muted-foreground">Pipeline</label>
          <select
            value={activePipelineId ?? ''}
            onChange={(e) => setPipelineId(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground"
          >
            {(pipelines ?? []).map((p: { id: string; name: string; is_default?: boolean }) => (
              <option key={p.id} value={p.id}>
                {p.name}
                {p.is_default ? ' (default)' : ''}
              </option>
            ))}
          </select>
        </div>
        {board && (
          <p className="text-sm text-muted-foreground">
            {board.total_leads} leads · {board.total_deals} deals ·{' '}
            <span className="font-semibold text-brand-teal-600">
              {formatCurrency(board.total_value_pence)}
            </span>
          </p>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-brand-teal-500" />
        </div>
      ) : (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
          <div className="flex snap-x gap-4 overflow-x-auto pb-4">
            {(board?.columns ?? []).map(
              (col: {
                stage: { id: string; name: string; is_won: boolean; is_lost: boolean }
                leads: BoardCard[]
                deals: BoardCard[]
              }) => {
                const cards: BoardCard[] = [...(col.leads ?? []), ...(col.deals ?? [])]
                const borderTone = col.stage.is_won
                  ? 'border-teal-300 bg-teal-50/50 dark:border-teal-800 dark:bg-teal-950/30'
                  : col.stage.is_lost
                    ? 'border-border bg-muted/30'
                    : 'border-brand-teal-300/40 bg-card dark:border-brand-teal-800/50'

                return (
                  <div
                    key={col.stage.id}
                    id={col.stage.id}
                    className={`w-[min(16rem,85vw)] flex-shrink-0 snap-start rounded-xl border-2 p-3 ${borderTone}`}
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-foreground">{col.stage.name}</h3>
                      <span className="rounded-full bg-background px-2 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">
                        {cards.length}
                      </span>
                    </div>
                    <SortableContext
                      items={cards.map(cardKey)}
                      strategy={verticalListSortingStrategy}
                      id={col.stage.id}
                    >
                      <div className="min-h-[5rem] space-y-2">
                        {cards.map((c) => (
                          <BoardCardItem key={cardKey(c)} card={c} onOpen={setSelectedCard} />
                        ))}
                      </div>
                    </SortableContext>
                  </div>
                )
              },
            )}
          </div>
        </DndContext>
      )}

      {selectedCard && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/30"
            aria-label="Close panel"
            onClick={() => setSelectedCard(null)}
          />
          <CrmBoardCardPanel card={selectedCard} onClose={() => setSelectedCard(null)} />
        </>
      )}
    </div>
  )
}
