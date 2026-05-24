import { LoyaltyBrandingProvider } from '@/components/loyalty-portal/LoyaltyBrandingProvider'
import { LoyaltyPortalShell } from '@/components/loyalty-portal/LoyaltyPortalShell'

export default function RewardsTenantLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { tenant: string }
}) {
  return (
    <LoyaltyBrandingProvider tenant={params.tenant}>
      <LoyaltyPortalShell tenant={params.tenant}>{children}</LoyaltyPortalShell>
    </LoyaltyBrandingProvider>
  )
}
