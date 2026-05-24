'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'

export function AuthGate({ tenant, children }: { tenant: string; children: React.ReactNode }) {
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated(tenant)) {
      router.replace(`/${tenant}/login`)
    }
  }, [tenant, router])

  if (!isAuthenticated(tenant)) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-sm text-slate-500">
        Checking sign-in…
      </div>
    )
  }

  return <>{children}</>
}
