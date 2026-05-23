'use client'

import { IndustryAddonWorkspace } from '@/components/addons/IndustryAddonWorkspace'

export default function IndustryCrmPage() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-semibold text-white">Industry CRM</h1>
      <IndustryAddonWorkspace tab="crm" />
    </div>
  )
}
