import type { ReactNode } from 'react'
import { CrmSubNav } from '@/components/crm/CrmSubNav'

export default function CrmLayout({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-5">
      <CrmSubNav />
      {children}
    </div>
  )
}
