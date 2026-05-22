'use client'

import type { ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { CrmSubNav } from '@/components/crm/CrmSubNav'

/** Hide sub-nav on CRM hub landing only; show on all detail routes. */
export default function CrmLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const isHub = pathname === '/dashboard/crm' || pathname === '/dashboard/crm/'

  return (
    <div className="space-y-5">
      {!isHub && <CrmSubNav />}
      {children}
    </div>
  )
}
