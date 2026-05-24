import type { Metadata, Viewport } from 'next'
import './loyalty-portal.css'
import { LoyaltyPWASetup } from '@/components/loyalty-portal/LoyaltyPWASetup'

export const metadata: Metadata = {
  title: { default: 'Rewards Wallet', template: '%s · Rewards' },
  description: 'Your loyalty rewards wallet',
  manifest: '/rewards/manifest.webmanifest',
  appleWebApp: { capable: true, statusBarStyle: 'default', title: 'Rewards' },
}

export const viewport: Viewport = {
  themeColor: '#2563EB',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RewardsRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="rewards-portal min-h-dvh bg-slate-50 text-slate-900">
      {children}
      <LoyaltyPWASetup />
    </div>
  )
}
