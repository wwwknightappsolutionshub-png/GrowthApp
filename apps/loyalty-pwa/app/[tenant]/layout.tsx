import { BrandingProvider } from '@/components/BrandingProvider'
import { LoyaltyShell } from '@/components/LoyaltyShell'

export default function TenantLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { tenant: string }
}) {
  return (
    <BrandingProvider tenant={params.tenant}>
      <LoyaltyShell tenant={params.tenant}>{children}</LoyaltyShell>
    </BrandingProvider>
  )
}
