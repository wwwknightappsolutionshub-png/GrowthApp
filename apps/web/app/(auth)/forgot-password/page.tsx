'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { auth } from '@/lib/api-client'
import { AuthPageHeader } from '@/components/brand/AuthPageHeader'
import { authPageTitle } from '@/components/brand/AuthJourneyHeadline'

const inputBase =
  'h-11 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0'

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit } = useForm<{ email: string }>()

  const onSubmit = async ({ email }: { email: string }) => {
    setLoading(true)
    try {
      await auth.forgotPassword(email)
      setSent(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="text-center">
        <div className="text-4xl mb-4">📧</div>
        <h2 className="font-display text-xl font-bold text-foreground mb-2">Check your inbox</h2>
        <p className="text-sm text-muted-foreground">
          If that email exists, we&apos;ve sent a reset link. Check your spam folder too.
        </p>
        <Link href="/login" className="mt-6 inline-block text-sm font-medium text-brand-forest-700 hover:underline">
          Back to login
        </Link>
      </div>
    )
  }

  return (
    <div>
      <AuthPageHeader
        eyebrow="Reset password"
        title={authPageTitle('Reset password')}
        description="Enter your email and we'll send a secure reset link."
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-foreground/80">
            Email address
          </label>
          <input
            {...register('email')}
            type="email"
            required
            className={inputBase}
            placeholder="you@business.com"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="h-11 w-full rounded-md bg-brand-forest-700 text-sm font-semibold text-brand-forest-foreground transition-colors hover:bg-brand-forest-800 disabled:opacity-50"
        >
          {loading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>

      <p className="mt-6 text-center">
        <Link href="/login" className="text-sm font-medium text-brand-forest-700 hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  )
}
