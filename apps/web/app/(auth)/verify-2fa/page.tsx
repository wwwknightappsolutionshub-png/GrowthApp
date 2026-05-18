'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast } from 'sonner'
import { auth } from '@/lib/api-client'
import { ShieldCheck } from 'lucide-react'

function Verify2FAForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const tempToken = searchParams.get('temp_token')

  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [isBackupCode, setIsBackupCode] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!tempToken) {
      router.replace('/login')
    }
    inputRef.current?.focus()
  }, [tempToken, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim() || !tempToken) return

    setLoading(true)
    try {
      await auth.verify2FA({ temp_token: tempToken, code: code.trim() })
      router.push('/dashboard')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid code. Please try again.'
      toast.error(msg)
      setCode('')
      inputRef.current?.focus()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex flex-col items-center mb-6">
        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
          <ShieldCheck className="w-7 h-7 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Two-factor verification</h2>
        <p className="text-gray-500 text-sm mt-1 text-center">
          {isBackupCode
            ? 'Enter one of your backup codes'
            : 'Enter the 6-digit code from your authenticator app'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input
            ref={inputRef}
            type="text"
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder={isBackupCode ? 'XXXX-XXXX-XXXX' : '000000'}
            maxLength={isBackupCode ? 14 : 6}
            autoComplete="one-time-code"
            inputMode={isBackupCode ? 'text' : 'numeric'}
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-center text-2xl tracking-[0.3em] font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading || code.length < 6}
          className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </form>

      <div className="mt-5 text-center">
        <button
          type="button"
          onClick={() => { setIsBackupCode(!isBackupCode); setCode('') }}
          className="text-sm text-blue-600 hover:underline"
        >
          {isBackupCode
            ? 'Use authenticator app instead'
            : "Can't access your app? Use a backup code"}
        </button>
      </div>

      <p className="mt-4 text-center text-xs text-gray-400">
        Open Google Authenticator, Microsoft Authenticator, or Authy to get your code.
      </p>
    </div>
  )
}

export default function Verify2FAPage() {
  return (
    <Suspense fallback={
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
            <ShieldCheck className="w-7 h-7 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Two-factor verification</h2>
          <p className="text-gray-500 text-sm mt-1">Loading...</p>
        </div>
      </div>
    }>
      <Verify2FAForm />
    </Suspense>
  )
}
