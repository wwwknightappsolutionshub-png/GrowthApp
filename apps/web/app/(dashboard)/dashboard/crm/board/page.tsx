'use client'

import { UnifiedPipelineBoard } from '@/components/crm/UnifiedPipelineBoard'
import { CrmDetailShell } from '@/components/crm/CrmDetailShell'

export default function CrmBoardPage() {
  return (
    <CrmDetailShell
      title="Pipeline"
      subtitle="Drag leads and deals across stages — send remarketing and upsell from each deal card"
      backHref="/dashboard/crm"
    >
      <UnifiedPipelineBoard />
    </CrmDetailShell>
  )
}
