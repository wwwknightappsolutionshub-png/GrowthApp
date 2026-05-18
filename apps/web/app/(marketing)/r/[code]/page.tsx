'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

export default function ReferralLandingPage() {
  const params = useParams()
  const code = String(params.code || '')
  const [logged, setLogged] = useState<string | null>(null)

  useEffect(() => {
    if (!code) return
    const url = `${API_BASE}/api/referrals/events/log`
    axios
      .post(url, { ref_code: code }, { withCredentials: true })
      .then((r) => setLogged(r.data?.id || 'ok'))
      .catch(() => setLogged('err'))
  }, [code])

  return (
    <div className="mx-auto max-w-lg px-6 py-16 text-center">
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Referral</p>
      <h1 className="mt-3 font-display text-2xl font-bold text-foreground">You&apos;re invited</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {logged && logged !== 'err'
          ? 'Your visit was recorded. Create an account to continue.'
          : 'Join CustomerFlow AI using the button below.'}
      </p>
      <Link
        href={`/register?ref=${encodeURIComponent(code)}`}
        className="mt-8 inline-flex h-11 items-center justify-center rounded-md bg-brand-forest-600 px-6 text-sm font-semibold text-white hover:bg-brand-forest-700"
      >
        Sign up with this referral
      </Link>
    </div>
  )
}
