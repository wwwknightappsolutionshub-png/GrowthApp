'use client'

import { useState } from 'react'
import { membershipRewards } from '@/lib/api-client'

export function MembershipInterestForm({
  tenantSlug,
  planId,
  planName,
}: {
  tenantSlug: string
  planId?: string
  planName?: string
}) {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')
    try {
      await membershipRewards.submitInterest(tenantSlug, {
        first_name: firstName,
        last_name: lastName || undefined,
        email: email || undefined,
        phone: phone || undefined,
        message: message || undefined,
        plan_id: planId,
      })
      setStatus('done')
      setFirstName('')
      setLastName('')
      setEmail('')
      setPhone('')
      setMessage('')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'done') {
    return (
      <p className="text-center text-emerald-800 font-medium py-6">
        Thank you! We&apos;ll contact you about membership soon.
      </p>
    )
  }

  return (
    <form onSubmit={onSubmit} className="max-w-md mx-auto space-y-3 text-left">
      {planName ? (
        <p className="text-sm text-gray-600 text-center">
          Enquiring about: <strong>{planName}</strong>
        </p>
      ) : null}
      <div className="grid sm:grid-cols-2 gap-3">
        <input
          required
          placeholder="First name *"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
        />
        <input
          placeholder="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
        />
      </div>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
      />
      <input
        placeholder="Phone"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
      />
      <textarea
        placeholder="Message (optional)"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        rows={3}
        className="w-full rounded-lg border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm placeholder:text-gray-400"
      />
      {status === 'error' && (
        <p className="text-sm text-red-600">Something went wrong. Please try again.</p>
      )}
      <button
        type="submit"
        disabled={status === 'loading'}
        className="w-full rounded-lg bg-emerald-800 text-white font-semibold py-2.5 text-sm hover:bg-emerald-900 disabled:opacity-50"
      >
        {status === 'loading' ? 'Sending…' : 'Request membership info'}
      </button>
    </form>
  )
}
