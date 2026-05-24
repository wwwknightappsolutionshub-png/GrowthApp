'use client'

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { loyaltyPortal, type Branding } from '@/lib/api-client'

type BrandingContextValue = {
  branding: Branding | null
  isLoading: boolean
  tenant: string
}

const BrandingContext = createContext<BrandingContextValue | null>(null)

export function BrandingProvider({ tenant, children }: { tenant: string; children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-branding', tenant],
    queryFn: () => loyaltyPortal.branding(tenant).then((r) => r.data),
    staleTime: 60_000,
  })

  useEffect(() => {
    if (data?.primary_color) {
      document.documentElement.style.setProperty('--tenant-primary', data.primary_color)
    }
  }, [data?.primary_color])

  const value = useMemo(
    () => ({ branding: data ?? null, isLoading, tenant }),
    [data, isLoading, tenant],
  )

  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>
}

export function useBranding() {
  const ctx = useContext(BrandingContext)
  if (!ctx) throw new Error('useBranding must be used within BrandingProvider')
  return ctx
}
