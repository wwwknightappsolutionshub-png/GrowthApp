'use client'

import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'

import { auth } from '@/lib/api-client'
import { fetchMe } from '@/lib/auth'

function VerifyContent() {
  const router = useRouter()
  const params = useSearchParams()
  const token = params.get('token')
  const next = params.get('next') ?? '/dashboard'
  const [state, setState] = useState<'verifying' | 'ok' | 'error'>('verifying')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError('No sign-in token in the link. Please request a new one.')
      setState('error')
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        await auth.verifyMagicLink(token)
        if (cancelled) return
        const me = await fetchMe()
        setState('ok')
        // Brief pause so the success state is visible.
        setTimeout(() => router.replace(me?.is_superadmin ? '/admin' : next), 600)
      } catch (err: any) {
        if (cancelled) return
        setError(err?.response?.data?.detail || 'This sign-in link is invalid or has expired.')
        setState('error')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, next, router])

  return (
    <div className="text-center max-w-sm mx-auto py-8">
      {state === 'verifying' && (
        <>
          <Loader2 className="w-10 h-10 mx-auto text-blue-600 animate-spin" />
          <h1 className="mt-6 text-xl font-bold text-gray-900">Signing you in…</h1>
          <p className="mt-2 text-sm text-gray-500">
            We're verifying your magic link. Hold tight for just a moment.
          </p>
        </>
      )}

      {state === 'ok' && (
        <>
          <div className="w-12 h-12 mx-auto rounded-full bg-emerald-100 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          </div>
          <h1 className="mt-6 text-xl font-bold text-gray-900">Welcome back!</h1>
          <p className="mt-2 text-sm text-gray-500">Redirecting to your dashboard…</p>
        </>
      )}

      {state === 'error' && (
        <>
          <div className="w-12 h-12 mx-auto rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <h1 className="mt-6 text-xl font-bold text-gray-900">Sign-in failed</h1>
          <p className="mt-2 text-sm text-gray-500">{error}</p>
          <Link
            href="/login"
            className="inline-block mt-6 px-5 py-2.5 text-sm font-semibold text-white bg-gray-900 rounded-xl hover:bg-gray-800"
          >
            Back to sign-in
          </Link>
        </>
      )}
    </div>
  )
}

export default function MagicLinkVerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      }
    >
      <VerifyContent />
    </Suspense>
  )
}
