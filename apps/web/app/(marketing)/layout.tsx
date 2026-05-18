/**
 * Marketing routes always render in the canonical light-mode brand palette,
 * regardless of the visitor's OS-level dark-mode preference. The dashboard
 * is where users can opt in to dark mode for their own workspace.
 */
import { SplashScreen } from '@/components/marketing/SplashScreen'
import { SupportChatWidget } from '@/components/marketing/SupportChatWidget'

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="surface-light bg-background text-foreground">
      <SplashScreen />
      {children}
      <SupportChatWidget />
    </div>
  )
}
