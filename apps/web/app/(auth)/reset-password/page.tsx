'use client'

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { auth } from '@/lib/api-client'

const schema = z
  .object({
    password: z
      .string()
      .min(8, 'At least 8 characters')
      .regex(/[A-Z]/, 'Include one uppercase letter')
      .regex(/[0-9]/, 'Include one number'),
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, {
    message: 'Passwords do not match',
    path: ['confirm'],
  })

type FormData = z.infer<typeof schema>

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')?.trim() ?? ''
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  if (!token) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-8 text-center shadow-lg">
        <h2 className="text-xl font-bold text-foreground mb-2">Invalid reset link</h2>
        <p className="text-sm text-muted-foreground mb-6">
          This link is missing a token. Request a new reset email from the login page.
        </p>
        <Link
          href="/forgot-password"
          className="inline-block text-sm font-semibold text-brand-teal-600 hover:underline"
        >
          Request new link
        </Link>
      </div>
    )
  }

  const onSubmit = async ({ password }: FormData) => {
    setLoading(true)
    try {
      await auth.resetPassword(token, password)
      setDone(true)
      toast.success('Password updated — you can sign in now')
      setTimeout(() => router.push('/login'), 2000)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not reset password. The link may have expired.'
      toast.error(typeof msg === 'string' ? msg : 'Reset failed')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-lg">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Password updated</h2>
        <p className="text-sm text-gray-500 mb-4">Redirecting you to sign in…</p>
        <Link href="/login" className="text-sm font-semibold text-blue-600 hover:underline">
          Sign in now
        </Link>
      </div>
    )
  }

  return (
    <div className="rounded-2xl bg-white p-8 shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose a new password</h2>
      <p className="text-sm text-gray-500 mb-6">
        Use at least 8 characters with one uppercase letter and one number.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
          <input
            {...register('password')}
            type="password"
            autoComplete="new-password"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.password && (
            <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
          <input
            {...register('confirm')}
            type="password"
            autoComplete="new-password"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.confirm && (
            <p className="mt-1 text-xs text-red-600">{errors.confirm.message}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving…' : 'Update password'}
        </button>
      </form>
      <p className="mt-4 text-center">
        <Link href="/login" className="text-sm text-blue-600 hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-2xl bg-white p-8 text-center shadow-lg text-sm text-gray-500">
          Loading…
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  )
}
