'use client'

import { Suspense } from 'react'
import { AccountsDashboard } from '@/components/accounts/AccountsDashboard'

export default function AccountsPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" /></div>}>
      <AccountsDashboard />
    </Suspense>
  )
}
