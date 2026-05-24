'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useLoyaltyBranding } from '@/components/loyalty-portal/LoyaltyBrandingProvider'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'
import { clearLoyaltyToken, rewardsPath } from '@/lib/loyalty-portal-auth'

export default function RewardsProfilePage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const router = useRouter()
  const qc = useQueryClient()
  const { branding } = useLoyaltyBranding()
  const { data } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortalCustomer.me(tenant).then((r) => r.data),
  })
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')

  const setPw = useMutation({
    mutationFn: () => loyaltyPortalCustomer.setPassword(tenant, password),
    onSuccess: () => {
      toast.success('Password updated')
      setPassword('')
      setConfirm('')
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
    },
    onError: () => toast.error('Could not update password'),
  })

  function logout() {
    clearLoyaltyToken(tenant)
    router.replace(rewardsPath(tenant, 'login'))
  }

  return (
    <LoyaltyAuthGate tenant={tenant}>
      <div className="space-y-4">
        <h1 className="text-lg font-semibold">Profile</h1>
        <section className="card space-y-1 text-sm">
          <p>
            <span className="text-slate-500">Name</span>{' '}
            <span className="font-medium">
              {data?.first_name} {data?.last_name ?? ''}
            </span>
          </p>
          {data?.email ? (
            <p>
              <span className="text-slate-500">Email</span>{' '}
              <span className="font-medium">{data.email}</span>
            </p>
          ) : null}
          <p>
            <span className="text-slate-500">Business</span>{' '}
            <span className="font-medium">{branding?.tenant_name}</span>
          </p>
        </section>

        {data?.must_change_password ? (
          <section className="card space-y-3">
            <h2 className="text-sm font-semibold">Set a new password</h2>
            <input
              type="password"
              className="input"
              placeholder="New password (min 8 chars)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <input
              type="password"
              className="input"
              placeholder="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
            <button
              type="button"
              className="btn-primary w-full"
              disabled={password.length < 8 || password !== confirm || setPw.isPending}
              onClick={() => setPw.mutate()}
            >
              Save password
            </button>
          </section>
        ) : null}

        <button type="button" className="btn-secondary w-full" onClick={logout}>
          Sign out
        </button>
      </div>
    </LoyaltyAuthGate>
  )
}
