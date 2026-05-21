'use client'

import { UnifiedPipelineBoard } from '@/components/crm/UnifiedPipelineBoard'

export default function CrmBoardPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">Pipeline</h1>
        <p className="text-sm text-muted-foreground">
          Drag leads and deals across stages — one board for your whole sales flow
        </p>
      </div>
      <UnifiedPipelineBoard />
    </div>
  )
}
