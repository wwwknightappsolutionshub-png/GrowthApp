'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { auth } from '@/lib/api-client'

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
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-4xl mb-4">📧</div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Check your inbox</h2>
        <p className="text-gray-500 text-sm">If that email exists, we've sent a reset link. Check your spam folder too.</p>
        <Link href="/login" className="mt-6 inline-block text-blue-600 text-sm hover:underline">Back to login</Link>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Reset your password</h2>
      <p className="text-sm text-gray-500 mb-6">Enter your email and we'll send a reset link.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
          <input {...register('email')} type="email" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="you@business.com" />
        </div>
        <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
          {loading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>
      <p className="mt-4 text-center"><Link href="/login" className="text-sm text-blue-600 hover:underline">Back to login</Link></p>
    </div>
  )
}
