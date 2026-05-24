'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useLoyaltyBranding } from '@/components/loyalty-portal/LoyaltyBrandingProvider'
import { isLoyaltyAuthenticated, rewardsPath, setLoyaltyToken } from '@/lib/loyalty-portal-auth'
import { loyaltyPortalCustomer } from '@/lib/api-client'

export default function RewardsLoginPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const router = useRouter()
  const { branding, isLoading } = useLoyaltyBranding()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'magic' | 'password'>('magic')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (isLoyaltyAuthenticated(tenant)) {
      router.replace(rewardsPath(tenant, 'dashboard'))
    }
  }, [tenant, router])

  async function sendMagicLink() {
    setBusy(true)
    try {
      await loyaltyPortalCustomer.requestMagicLink(tenant, email.trim())
      toast.success('Check your email for a sign-in link')
    } catch {
      toast.error('Could not send sign-in link')
    } finally {
      setBusy(false)
    }
  }

  async function loginWithPassword() {
    setBusy(true)
    try {
      const { data } = await loyaltyPortalCustomer.login(tenant, email.trim(), password)
      setLoyaltyToken(tenant, data.access_token)
      router.replace(rewardsPath(tenant, 'dashboard'))
    } catch {
      toast.error('Invalid email or password')
    } finally {
      setBusy(false)
    }
  }

  if (isLoading) {
    return <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>
  }

  if (!branding?.loyalty_enabled) {
    return (
      <div className="card">
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Rewards are not available for {branding?.tenant_name ?? 'this business'} yet.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm space-y-4 pt-8">
      <div className="text-center">
        <h1 className="text-xl font-bold text-brand">{branding.tenant_name}</h1>
        <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">Sign in to your rewards wallet</p>
        <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
          Use the magic link from your welcome email, or request a new one below.
        </p>
      </div>

      <div className="card space-y-3">
        <input
          type="email"
          className="input"
          placeholder="Email address"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        {mode === 'password' ? (
          <input
            type="password"
            className="input"
            placeholder="Password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        ) : null}

        {mode === 'magic' ? (
          <button
            type="button"
            className="btn-primary w-full"
            disabled={!email.trim() || busy}
            onClick={() => void sendMagicLink()}
          >
            Email me a sign-in link
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary w-full"
            disabled={!email.trim() || !password || busy}
            onClick={() => void loginWithPassword()}
          >
            Sign in
          </button>
        )}

        <button
          type="button"
          className="w-full text-center text-xs text-[hsl(var(--muted-foreground))] underline"
          onClick={() => setMode(mode === 'magic' ? 'password' : 'magic')}
        >
          {mode === 'magic' ? 'Use password instead' : 'Use magic link instead'}
        </button>
      </div>
    </div>
  )
}
