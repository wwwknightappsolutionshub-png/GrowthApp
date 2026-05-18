'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auth } from '@/lib/api-client'
import { toast } from 'sonner'
import { ShieldCheck, ShieldOff, Copy, Check } from 'lucide-react'
import { useForm } from 'react-hook-form'

export function TwoFactorSettings() {
  const qc = useQueryClient()
  const [step, setStep] = useState<'idle' | 'setup' | 'backup'>('idle')
  const [setupData, setSetupData] = useState<{ secret: string; qr_code_image_url: string } | null>(null)
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [copied, setCopied] = useState(false)

  const { data: meData } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then(r => r.data),
  })

  const { register: regEnable, handleSubmit: hsEnable, formState: { errors: errEnable }, reset: resetEnable } = useForm<{ code: string }>()
  const { register: regDisable, handleSubmit: hsDisable, formState: { errors: errDisable }, reset: resetDisable } = useForm<{ password: string; code: string }>()

  const setupMutation = useMutation({
    mutationFn: () => auth.setup2FA(),
    onSuccess: (res) => {
      setSetupData(res.data)
      setStep('setup')
    },
    onError: () => toast.error('Failed to start 2FA setup'),
  })

  const enableMutation = useMutation({
    mutationFn: (data: { code: string }) => auth.enable2FA(data),
    onSuccess: (res) => {
      setBackupCodes(res.data.backup_codes)
      setStep('backup')
      qc.invalidateQueries({ queryKey: ['me'] })
      toast.success('Two-factor authentication enabled!')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Invalid code'),
  })

  const disableMutation = useMutation({
    mutationFn: (data: { password: string; code: string }) => auth.disable2FA(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      resetDisable()
      toast.success('Two-factor authentication disabled')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Could not disable 2FA'),
  })

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const is2FAEnabled = meData?.totp_enabled

  if (step === 'backup' && backupCodes.length > 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-green-700">
          <ShieldCheck className="w-5 h-5" />
          <h3 className="font-semibold">2FA enabled — save your backup codes</h3>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800 mb-3">
            <strong>Save these now.</strong> Each code can only be used once if you lose access to your authenticator app. They won't be shown again.
          </p>
          <div className="grid grid-cols-2 gap-2 mb-3">
            {backupCodes.map(code => (
              <div key={code} className="bg-white border border-yellow-300 rounded px-3 py-1.5 font-mono text-sm text-center">
                {code}
              </div>
            ))}
          </div>
          <button
            onClick={copyBackupCodes}
            className="flex items-center gap-1.5 text-sm text-yellow-800 hover:text-yellow-900"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy all codes'}
          </button>
        </div>
        <button
          onClick={() => { setStep('idle'); setBackupCodes([]); setSetupData(null) }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Done — I've saved my codes
        </button>
      </div>
    )
  }

  if (step === 'setup' && setupData) {
    return (
      <div className="space-y-5">
        <h3 className="font-semibold text-gray-900">Set up authenticator app</h3>
        <ol className="space-y-4 text-sm text-gray-600">
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
            Install <strong className="text-gray-900">Google Authenticator</strong>, <strong className="text-gray-900">Microsoft Authenticator</strong>, or <strong className="text-gray-900">Authy</strong>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
            Scan the QR code or enter the secret manually
          </li>
        </ol>

        <div className="flex flex-col items-center gap-4 py-2">
          <img
            src={setupData.qr_code_image_url}
            alt="2FA QR Code"
            className="w-48 h-48 border border-gray-200 rounded-lg"
          />
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Manual entry key:</p>
            <code className="text-sm font-mono bg-gray-100 px-3 py-1 rounded select-all">
              {setupData.secret}
            </code>
          </div>
        </div>

        <form onSubmit={hsEnable(d => enableMutation.mutate(d))} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Enter the 6-digit code from your app to confirm
            </label>
            <input
              {...regEnable('code', { required: 'Code is required', pattern: { value: /^\d{6}$/, message: 'Must be 6 digits' } })}
              placeholder="000000"
              maxLength={6}
              inputMode="numeric"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-center tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errEnable.code && <p className="mt-1 text-xs text-red-500">{errEnable.code.message}</p>}
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={enableMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {enableMutation.isPending ? 'Verifying...' : 'Enable 2FA'}
            </button>
            <button
              type="button"
              onClick={() => { setStep('idle'); setSetupData(null); resetEnable() }}
              className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    )
  }

  // Idle state — show current status
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {is2FAEnabled
            ? <ShieldCheck className="w-5 h-5 text-green-500" />
            : <ShieldOff className="w-5 h-5 text-gray-400" />}
          <div>
            <p className="font-medium text-sm text-gray-900">Two-factor authentication</p>
            <p className="text-xs text-gray-500">
              {is2FAEnabled
                ? 'Your account is protected with an authenticator app'
                : 'Add an extra layer of security to your account'}
            </p>
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${is2FAEnabled ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {is2FAEnabled ? 'Enabled' : 'Disabled'}
        </span>
      </div>

      {!is2FAEnabled ? (
        <button
          onClick={() => setupMutation.mutate()}
          disabled={setupMutation.isPending}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {setupMutation.isPending ? 'Setting up...' : 'Set up 2FA'}
        </button>
      ) : (
        <form onSubmit={hsDisable(d => disableMutation.mutate(d))} className="space-y-3 pt-2 border-t border-gray-100">
          <p className="text-sm text-gray-600 font-medium">Disable 2FA — requires your password and a code</p>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Password</label>
            <input
              {...regDisable('password', { required: 'Required' })}
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errDisable.password && <p className="mt-1 text-xs text-red-500">{errDisable.password.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Authenticator code</label>
            <input
              {...regDisable('code', { required: 'Required', pattern: { value: /^\d{6}$/, message: '6 digits' } })}
              placeholder="000000"
              maxLength={6}
              inputMode="numeric"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errDisable.code && <p className="mt-1 text-xs text-red-500">{errDisable.code.message}</p>}
          </div>
          <button
            type="submit"
            disabled={disableMutation.isPending}
            className="border border-red-300 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50 disabled:opacity-50"
          >
            {disableMutation.isPending ? 'Disabling...' : 'Disable 2FA'}
          </button>
        </form>
      )}
    </div>
  )
}
