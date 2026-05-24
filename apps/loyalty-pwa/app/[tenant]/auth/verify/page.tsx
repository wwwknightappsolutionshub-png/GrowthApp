'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { setToken } from '@/lib/auth'
import { loyaltyPortal } from '@/lib/api-client'

function VerifyInner({ tenant }: { tenant: string }) {
  const router = useRouter()
  const params = useSearchParams()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = params.get('token')
    const tenantParam = params.get('tenant')
    if (!token) {
      setError('Missing sign-in token')
      return
    }
    const slug = tenantParam || tenant
    loyaltyPortal
      .verifyMagicLink(slug, token)
      .then(({ data }) => {
        setToken(slug, data.access_token)
        const next = params.get('next')
        router.replace(next ? decodeURIComponent(next) : `/${slug}/dashboard`)
      })
      .catch(() => {
        setError('This sign-in link is invalid or has expired.')
      })
  }, [params, router, tenant])

  if (error) {
    return (
      <div className="card mx-auto max-w-sm text-center text-sm text-red-600">
        {error}
      </div>
    )
  }

  return <p className="text-center text-sm text-slate-500">Signing you in…</p>
}

export default function VerifyPage({ params }: { params: { tenant: string } }) {
  return (
    <Suspense fallback={<p className="text-center text-sm text-slate-500">Loading…</p>}>
      <VerifyInner tenant={params.tenant} />
    </Suspense>
  )
}
