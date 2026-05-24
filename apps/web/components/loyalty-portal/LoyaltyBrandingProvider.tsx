'use client'

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { loyaltyPortalCustomer, type LoyaltyPortalBranding } from '@/lib/api-client'

type BrandingContextValue = {
  branding: LoyaltyPortalBranding | null
  isLoading: boolean
  tenant: string
}

const BrandingContext = createContext<BrandingContextValue | null>(null)

export function LoyaltyBrandingProvider({ tenant, children }: { tenant: string; children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-branding', tenant],
    queryFn: () => loyaltyPortalCustomer.branding(tenant).then((r) => r.data),
    staleTime: 60_000,
  })

  useEffect(() => {
    const primary = data?.primary_color || '#025422'
    document.documentElement.style.setProperty('--tenant-primary', primary)
    /* Keep global wallet buttons on brand forest; tenant color accents progress/UI */
  }, [data?.primary_color])

  const value = useMemo(
    () => ({ branding: data ?? null, isLoading, tenant }),
    [data, isLoading, tenant],
  )

  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>
}

export function useLoyaltyBranding() {
  const ctx = useContext(BrandingContext)
  if (!ctx) throw new Error('useLoyaltyBranding must be used within LoyaltyBrandingProvider')
  return ctx
}
